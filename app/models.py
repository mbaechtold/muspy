# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Alexander Kojevnikov <alexander@kojevnikov.com>
#
# muspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# muspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with muspy.  If not, see <http://www.gnu.org/licenses/>.
import random
import string
from smtplib import SMTPException

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.db import IntegrityError
from django.db import models
from django.db import transaction
from django.db.backends.signals import connection_created
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from pylast import MalformedResponseError
from pylast import WSError

import app.musicbrainz as mb
from app import tasks
from app.tools import date_to_iso8601
from app.tools import date_to_str
from app.tools import str_to_date


class Artist(models.Model):

    mbid = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=512)
    sort_name = models.CharField(max_length=512)
    disambiguation = models.CharField(max_length=512, blank=True)
    users = models.ManyToManyField(User, through="UserArtist")
    last_check_for_releases = models.DateTimeField(null=True, blank=True)

    blacklisted = [
        "89ad4ac3-39f7-470e-963a-56509c546377",  # Various Artists
        "fe5b7087-438f-4e7e-afaf-6d93c8c888b2",
        "0677ef60-6be5-4e36-9d1e-8bb2bf85b981",
        "b7c7dfd9-d735-4733-9b10-f060ac75bd6a",
        "b05cc773-4e8e-40bc-ae12-dc88dfc2c9ec",
        "4b2228f5-e18b-4acc-ace7-b8db13a9306f",
        "046c889d-5b1c-4f54-9c7b-319a8f67e729",
        "1bf34db2-8447-4ecd-9b25-57945b28ef28",
        "023671ff-b1ad-4133-a4f3-aadaaadfd2e0",
        "f731ccc4-e22a-43af-a747-64213329e088",  # [anonymous]
        "33cf029c-63b0-41a0-9855-be2a3665fb3b",  # [data]
        "314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc",  # [dialogue]
        "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61",  # [no artist]
        "9be7f096-97ec-4615-8957-8d40b5dcbc41",  # [traditional]
        "125ec42a-7229-4250-afc5-e057484327fe",  # [unknown]
        "203b6058-2401-4bf0-89e3-8dc3d37c3f12",
        "5e760f5a-ea55-4b53-a18f-021c0d9779a6",
        "1d8bc797-ec8a-40d2-8d80-b1346b56a65f",
        "7734d67f-44d9-4ba2-91e3-9b067263210e",
        "f49cc9f4-dc00-48ab-9aab-6387c02738cf",
        "0035056d-72ac-41fa-8ea6-0e27e55f42f7",
        "d6bd72bc-b1e2-4525-92aa-0f853cbb41bf",  # [soundtrack]
    ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("artist", args=[self.mbid])

    class Blacklisted(Exception):
        pass

    class Unknown(Exception):
        pass

    @classmethod
    def get_by_mbid(cls, mbid):
        """
        Returns the artist having the given mbid. Fetch the artist from MusicBrainz if the artist
        does not yet exist in Muspy.
        """
        if mbid in cls.blacklisted:
            raise cls.Blacklisted()

        try:
            return cls.objects.get(mbid=mbid)
        except cls.DoesNotExist:
            pass

        artist_data = mb.get_artist(mbid)
        if artist_data is None:
            return None
        if not artist_data:
            raise cls.Unknown

        artist = Artist(
            mbid=mbid,
            name=artist_data["name"],
            sort_name=artist_data["sort-name"],
            disambiguation=artist_data.get("disambiguation", ""),
        )
        try:
            artist.save()
        except IntegrityError:
            # The artist was added while we were querying MB.
            return cls.objects.get(mbid=mbid)

        # Fetch a few release when a new artist has been added.
        artist.get_release_groups(limit=11)

        return artist

    def get_release_groups(self, limit=100_000):
        """
        Fetch the release groups for the artist from MusicBrainz. This might take a few second, so it
        better be called asynchronously. Make sure to not call this method too frequently or you get
        banned from MusicBrainz.
        """
        release_groups = mb.get_release_groups(self.mbid, limit=limit, offset=0)
        if release_groups:
            for rg_data in release_groups:
                # Ignoring releases without a release date or a type.
                if rg_data.get("first-release-date") and rg_data.get("type"):
                    release_date = str_to_date(rg_data["first-release-date"])
                    release_group, created = ReleaseGroup.objects.get_or_create(
                        artist=self,
                        mbid=rg_data["id"],
                        defaults={"date": release_date, "is_deleted": False},  # Used when creating.
                    )
                    release_group.name = rg_data["title"]
                    release_group.type = rg_data["type"]
                    release_group.date = release_date
                    release_group.save()

        return True

    @classmethod
    def get_by_user(cls, user):
        # TODO: paging
        return cls.objects.filter(users=user).order_by("sort_name")[:4000]


class Job(models.Model):

    ADD_ARTIST = 1
    ADD_RELEASE_GROUPS = 2
    GET_COVER = 3
    IMPORT_LASTFM = 4

    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, blank=True)
    type = models.IntegerField()
    data = models.TextField()

    @classmethod
    def add_artists(cls, user, names):
        with transaction.atomic():
            for name in names:
                cls(user=user, type=cls.ADD_ARTIST, data=name).save()

    @classmethod
    def add_release_groups(cls, artist):
        cls(user=None, type=cls.ADD_RELEASE_GROUPS, data=artist.mbid).save()

    @classmethod
    def get_cover(cls, mbid):
        cls(user=None, type=cls.GET_COVER, data=mbid).save()

    @classmethod
    def import_lastfm(cls, user, username, count, period):
        data = str(count) + "," + period + "," + username
        cls(user=user, type=cls.IMPORT_LASTFM, data=data).save()

    @classmethod
    def importing_artists(cls, user):
        """Returns a comma-separated list of all artists yet to be imported."""
        q = cls.objects.filter(user=user)
        q = q.filter(type=cls.ADD_ARTIST)
        return [r.data for r in q]

    @classmethod
    def has_import_lastfm(cls, user):
        return cls.objects.filter(user=user).filter(type=cls.IMPORT_LASTFM).exists()


class Notification(models.Model):
    class Meta:
        db_table = "app_notification"
        unique_together = ("user", "release_group")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    release_group = models.ForeignKey("ReleaseGroup", on_delete=models.CASCADE)


class ReleaseGroup(models.Model):
    """De-normalised release groups

    A release group can have different artists. Instead of adding a
    many-to-many relationship between them, keep everything in one
    table and group by mbid as needed.

    """

    FALLBACK_COVER_ART_URL = "https://via.placeholder.com/250x250.png?text=NOT FOUND"

    class Meta:
        unique_together = ("artist", "mbid")

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    mbid = models.CharField(max_length=36)
    name = models.CharField(max_length=512)
    type = models.CharField(max_length=16)
    date = models.IntegerField()  # 20080101 OR 20080100 OR 20080000
    is_deleted = models.BooleanField()
    cover_art_url = models.URLField(blank=True)
    last_check_for_cover_art = models.DateTimeField(null=True, blank=True)

    # TODO: This seems not to be used anywhere. Remove it!
    users_who_starred = models.ManyToManyField(
        User, through="Star", related_name="starred_release_groups"
    )
    # TODO: This seems not to be used anywhere. Remove it!
    users_to_notify = models.ManyToManyField(
        User, through="Notification", related_name="new_release_groups"
    )

    def __str__(self):
        return self.name

    def date_str(self):
        return date_to_str(self.date)

    def date_iso8601(self):
        return date_to_iso8601(self.date)

    @classmethod
    def get(cls, artist=None, user=None, limit=0, offset=0, feed=False):
        if not artist and not user:
            assert "Both artist and user are None"
            return None

        queryset = cls.objects.exclude(is_deleted=True).order_by("-date")

        if artist:
            queryset = queryset.filter(artist=artist)

        if user:
            # Only include release of artists the user is following.
            queryset = queryset.filter(
                artist_id__in=Subquery(
                    UserArtist.objects.filter(user=user)
                    .filter(artist_id=OuterRef("artist_id"))
                    .values("artist_id")
                )
            )

            # Only include release types the user has configured in the settings.
            profile = user.profile
            types = profile.get_types()
            # If the user is not tracking any release types, no releases will be shown.
            # TODO: Warn the user if she's not tracking any release types.
            queryset = queryset.filter(type__in=types)

            if feed and profile.legacy_id:
                # Don't include release groups added during the import
                # TODO: Feel free to remove this check some time in 2013.
                queryset = queryset.filter(is_gt=261_202)

            # Get the starred releases of the users. Starred releases will be shown before the other releases.
            queryset = queryset.annotate(
                is_starred=Coalesce(
                    Subquery(
                        Star.objects.filter(release_group_id=OuterRef("id"))
                        .filter(user=user)
                        .values("id")
                    ),
                    0,
                )
            )
            queryset = queryset.order_by("-is_starred", "-date")

        return queryset[offset : offset + limit]

    @classmethod
    def get_calendar(cls, date, limit, offset):
        """Returns the list of release groups for the date."""
        q = cls.objects.filter(date__lte=date)
        q = q.select_related("artist")
        # Calendar uses the same template as releases, adapt to conform.
        q = q.extra(
            select={
                "artist_mbid": '"app_artist"."mbid"',
                "artist_name": '"app_artist"."name"',
                "artist_sort_name": '"app_artist"."sort_name"',
                "artist_disambiguation": '"app_artist"."disambiguation"',
            }
        )
        q = q.filter(is_deleted=False)
        q = q.order_by("-date")
        return q[offset : offset + limit]

    @property
    def cover_url(self):
        # TODO: Prevent hammering.
        tasks.update_cover_art_by_mbid.delay(self.mbid)
        return self.cover_art_url or "https://via.placeholder.com/250x250.png?text=LOADING"

    def update_cover_art_url(self):
        """
        Fetch the release groups for the artist from MusicBrainz or Last.fm. This might take a few
        second, so it better be called asynchronously. Make sure to not call this method too frequently
        or you get banned from MusicBrainz or Last.fm.
        """
        # Attempt 1: Get cover url from the Cover Art Archive
        response = requests.get(
            f"https://coverartarchive.org/release-group/{self.mbid}/front-250",
            allow_redirects=False,
        )
        if response.status_code == 307:
            cover_art_url = response.headers["Location"]
            self.cover_art_url = cover_art_url
            self.save()
            return cover_art_url

        # Attempt 2: Get the cover url from Last.fm
        lastfm_client = settings.LASTFM_CLIENT
        releases = mb.get_releases(self.mbid, limit=10)
        for release in releases:
            try:
                album = lastfm_client.get_album_by_mbid(release["id"])
            except (WSError, MalformedResponseError):
                self.cover_art_url = self.FALLBACK_COVER_ART_URL
                self.save()
                return self.FALLBACK_COVER_ART_URL
            cover_art_url = album.get_cover_image()
            if cover_art_url:
                self.cover_art_url = cover_art_url
                self.save()
                return cover_art_url

        self.cover_art_url = self.FALLBACK_COVER_ART_URL
        self.save()
        return self.cover_art_url


class Star(models.Model):
    class Meta:
        db_table = "app_star"
        unique_together = ("user", "release_group")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    release_group = models.ForeignKey(ReleaseGroup, on_delete=models.CASCADE)

    @classmethod
    def set(cls, user, id, value):
        try:
            release_group = ReleaseGroup.objects.get(id=id)
        except ReleaseGroup.DoesNotExist:
            return
        if value:
            cls.objects.get_or_create(user=user, release_group=release_group)
        else:
            cls.objects.filter(user=user, release_group=release_group).delete()


class UserArtist(models.Model):
    class Meta:
        unique_together = ("user", "artist")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_artists")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get(cls, user, artist):
        try:
            return cls.objects.get(user=user, artist=artist)
        except cls.DoesNotExist:
            return None

    @classmethod
    def add(cls, user, artist):
        user_artist = cls(user=user, artist=artist)
        try:
            user_artist.save()
        except IntegrityError:
            pass

    @classmethod
    def remove(cls, user, mbids):
        with transaction.atomic():
            for mbid in mbids:
                q = cls.objects.filter(user=user)
                q = q.filter(artist__mbid=mbid)
                q.delete()


class UserProfile(models.Model):

    code_length = 16

    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)

    notify = models.BooleanField(default=True)
    notify_album = models.BooleanField(default=True)
    notify_single = models.BooleanField(default=True)
    notify_ep = models.BooleanField(default=True)
    notify_live = models.BooleanField(default=True)
    notify_compilation = models.BooleanField(default=True)
    notify_remix = models.BooleanField(default=True)
    notify_other = models.BooleanField(default=True)
    email_activated = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=code_length)
    reset_code = models.CharField(max_length=code_length)
    legacy_id = models.IntegerField(null=True)

    def get_types(self):
        """Return the list of release types the user wants to follow."""
        types = []
        if self.notify_album:
            types.append("Album")
        if self.notify_single:
            types.append("Single")
        if self.notify_ep:
            types.append("EP")
        if self.notify_live:
            types.append("Live")
        if self.notify_compilation:
            types.append("Compilation")
        if self.notify_remix:
            types.append("Remix")
        if self.notify_other:
            types.extend(["Soundtrack", "Spokenword", "Interview", "Audiobook", "Other"])
        return types

    def generate_code(self):
        code_chars = "23456789abcdefghijkmnpqrstuvwxyz"
        return "".join(random.choice(code_chars) for i in range(UserProfile.code_length))

    def purge(self):
        user = self.user
        with transaction.atomic():
            Job.objects.filter(user=user).delete()
            Notification.objects.filter(user=user).delete()
            Star.objects.filter(user=user).delete()
            UserArtist.objects.filter(user=user).delete()
            UserSearch.objects.filter(user=user).delete()
            self.delete()
            # Cannot call user.delete() because it references deprecated auth_message.
            cursor = connection.cursor()
            cursor.execute("DELETE FROM auth_user WHERE id=%s", [user.id])

    def send_email(self, subject, text_template, html_template, **kwds):
        text = render_to_string(text_template, kwds)
        msg = EmailMultiAlternatives(
            subject,
            text,
            "muspy@baechtold.me",
            [self.user.email],
            headers={"From": "muspy.baechtold.me <muspy@baechtold.me>"},
        )
        if html_template:
            html = render_to_string(html_template, kwds)
            msg.attach_alternative(html, "text/html")
        try:
            msg.send()
        except SMTPException:
            return False
        return True

    def send_activation_email(self):
        code = self.generate_code()
        self.activation_code = code
        self.save()
        self.send_email(
            subject="Email Activation",
            text_template="email/activate.txt",
            html_template=None,
            code=code,
        )

    def send_reset_email(self):
        code = self.generate_code()
        self.reset_code = code
        self.save()
        self.send_email(
            subject="Password Reset Confirmation",
            text_template="email/reset.txt",
            html_template=None,
            code=code,
        )

    def unsubscribe(self):
        self.notify = False
        self.save()

    @classmethod
    def activate(cls, code):
        profiles = UserProfile.objects.filter(activation_code=code)
        if not profiles:
            return False
        profile = profiles[0]
        profile.activation_code = ""
        profile.email_activated = True
        profile.save()
        return True

    @classmethod
    def reset(cls, code):
        profiles = UserProfile.objects.filter(reset_code=code)
        if not profiles:
            return None, None
        profile = profiles[0]
        password = User.objects.make_random_password(length=16)
        profile.reset_code = ""
        profile.user.set_password(password)
        with transaction.atomic():
            profile.user.save()
            profile.save()
        return profile.user.email, password

    @classmethod
    def get_by_email(cls, email):
        # We can have multiple users having the same email address.
        users = User.objects.filter(email=email.lower())
        if not users:
            return None
        try:
            return users[0].profile
        except UserProfile.DoesNotExist:
            return None

    @classmethod
    def get_by_legacy_id(cls, legacy_id):
        profiles = cls.objects.filter(legacy_id=legacy_id)
        return profiles[0] if profiles else None

    @classmethod
    def get_by_username(cls, username):
        # TODO: The usernames should be unique, so there can only be one user. Use "get()" instead of "filter()".
        users = User.objects.filter(username=username)
        if not users:
            return None
        try:
            return users[0].profile
        except UserProfile.DoesNotExist:
            return None

    @classmethod
    def create_user(cls, email, password):
        chars = string.ascii_lowercase + string.digits
        username = "".join(random.choice(chars) for i in range(30))
        return User.objects.create_user(username, email, password)


class UserSearch(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search = models.CharField(max_length=512)

    @classmethod
    def get(cls, user):
        return cls.objects.filter(user=user)

    @classmethod
    def remove(cls, user, searches):
        with transaction.atomic():
            for search in searches:
                cls.objects.filter(user=user, search=search).delete()


# Activate foreign keys for sqlite.
@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=1;")


# Create a profile for each user.
@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()


User.__unicode__ = lambda x: x.email
