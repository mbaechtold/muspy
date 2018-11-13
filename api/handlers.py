# -*- coding: utf-8 -*-
#
# Copyright © 2011 Alexander Kojevnikov <alexander@kojevnikov.com>
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

from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.resource import Resource
from piston.utils import rc

from app import lastfm
from app.models import *


class ApiResource(Resource):
    """TODO: Remove after upgrading to django-piston >= 0.2.3"""

    def __init__(self, handler, authentication=None):
        super(ApiResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, "csrf_exempt", True)


class ArtistHandler(AnonymousBaseHandler):
    allowed_methods = ("GET",)

    def read(self, request, mbid):
        try:
            artist = Artist.objects.get(mbid=mbid)
        except Artist.DoesNotExist:
            return rc.NOT_HERE

        return {
            "mbid": artist.mbid,
            "name": artist.name,
            "sort_name": artist.sort_name,
            "disambiguation": artist.disambiguation,
        }


class ArtistsHandler(BaseHandler):
    allowed_methods = ("GET", "PUT", "DELETE")

    def read(self, request, userid, mbid):
        if request.user.username != userid:
            return rc.FORBIDDEN

        artists = Artist.get_by_user(user=request.user)
        return [
            {
                "mbid": artist.mbid,
                "name": artist.name,
                "sort_name": artist.sort_name,
                "disambiguation": artist.disambiguation,
            }
            for artist in artists
        ]

    def update(self, request, userid, mbid):
        if request.user.username != userid:
            return rc.FORBIDDEN

        if mbid:
            try:
                artist = Artist.get_by_mbid(mbid)
            except (Artist.Blacklisted, Artist.Unknown):
                return rc.BAD_REQUEST
            if not artist:
                return rc.NOT_FOUND

            UserArtist.add(request.user, artist)
            response = rc.ALL_OK
            response.content = {
                "mbid": artist.mbid,
                "name": artist.name,
                "sort_name": artist.sort_name,
                "disambiguation": artist.disambiguation,
            }
            return response

        import_from = request.POST.get("import", "")
        username = request.POST.get("username", "")
        count = min(500, max(0, int(request.POST.get("count", 0))))
        period = request.POST.get("period", "")

        if (
            import_from != "last.fm"
            or not username
            or not count
            or period not in ["overall", "12month", "6month", "3month", "7day"]
        ):
            return rc.BAD_REQUEST

        if Job.has_import_lastfm(request.user) or Job.importing_artists(request.user):
            response = rc.THROTTLED
            response.write(
                ": The user already has a pending import. "
                "Please wait until the import finishes before importing again."
            )
            return response

        if not lastfm.has_user(username):
            response = rc.BAD_REQUEST
            response.write(": Unknown user: %s" % username)
            return response

        Job.import_lastfm(request.user, username, count, period)
        return rc.ALL_OK

    def delete(self, request, userid, mbid):
        if request.user.username != userid:
            return rc.FORBIDDEN

        if not mbid:
            return rc.BAD_REQUEST

        UserArtist.remove(user=request.user, mbids=[mbid])
        return rc.DELETED


class ReleaseHandler(AnonymousBaseHandler):
    allowed_methods = ("GET",)

    def read(self, request, mbid):
        q = ReleaseGroup.objects.select_related("artist")
        q = q.filter(mbid=mbid)
        q = q.filter(is_deleted=False)
        releases = list(q)
        if not releases:
            return rc.NOT_HERE

        release = releases[0]
        artists = [release.artist for release in releases]
        return {
            "mbid": release.mbid,
            "name": release.name,
            "type": release.type,
            "date": release.date_str(),
            "artists": [
                {
                    "mbid": artist.mbid,
                    "name": artist.name,
                    "sort_name": artist.sort_name,
                    "disambiguation": artist.disambiguation,
                }
                for artist in artists
            ],
        }


class ReleasesHandler(AnonymousBaseHandler):
    allowed_methods = ("GET",)

    def read(self, request, userid):
        artist = user = None
        if userid:
            try:
                user = User.objects.get(username=userid)
            except User.DoesNotExist:
                return rc.NOT_HERE

        limit = min(100, max(0, int(request.GET.get("limit", 40))))
        offset = max(0, int(request.GET.get("offset", 0)))
        mbid = request.GET.get("mbid", "")
        since = request.GET.get("since", "")

        if mbid:
            try:
                artist = Artist.get_by_mbid(mbid)
            except (Artist.Blacklisted, Artist.Unknown):
                return rc.BAD_REQUEST
            if not artist:
                return rc.NOT_HERE

        if since:
            try:
                release = ReleaseGroup.objects.get(mbid=since)
            except ReleaseGroup.DoesNotExist:
                return rc.NOT_HERE
            q = ReleaseGroup.objects.filter(id__gt=release.id)
            if user:
                q = q.filter(artist__users=user)
            q = q.filter(is_deleted=False)
            q = q.order_by("id")
            q = q.select_related("artist")
            q = q.extra(
                select={
                    "artist_mbid": '"app_artist"."mbid"',
                    "artist_name": '"app_artist"."name"',
                    "artist_sort_name": '"app_artist"."sort_name"',
                    "artist_disambiguation": '"app_artist"."disambiguation"',
                }
            )
            releases = q[:limit]
        elif artist or user:
            releases = ReleaseGroup.get(artist=artist, user=user, limit=limit, offset=offset)
        else:
            today = int(date.today().strftime("%Y%m%d"))
            releases = ReleaseGroup.get_calendar(date=today, limit=limit, offset=offset)

        return [
            {
                "mbid": release.mbid,
                "name": release.name,
                "type": release.type,
                "date": release.date_str(),
                "artist": {
                    "mbid": release.artist_mbid,
                    "name": release.artist_name,
                    "sort_name": release.artist_sort_name,
                    "disambiguation": release.artist_disambiguation,
                },
            }
            for release in releases
        ]


class AnonymousUserHandler(AnonymousBaseHandler):
    allowed_methods = "POST"

    def create(self, request, userid):
        email = request.POST.get("email", "").lower().strip()
        password = request.POST.get("password", "")
        activate = int(request.POST.get("activate", "0"))

        if not email:
            response = rc.BAD_REQUEST
            response.write(": empty email address")
            return response

        if not password:
            response = rc.BAD_REQUEST
            response.write(": empty password")
            return response

        if UserProfile.get_by_email(email):
            response = rc.BAD_REQUEST
            response.write(": email already in use")
            return response

        user = UserProfile.create_user(email, password)

        if activate:
            user.profile.send_activation_email()

        return rc.CREATED


class UserHandler(BaseHandler):
    allowed_methods = ("GET", "POST", "PUT", "DELETE")
    anonymous = AnonymousUserHandler

    def read(self, request, userid):
        if userid and request.user.username != userid:
            return rc.BAD_REQUEST

        user = request.user
        profile = user.profile

        return {
            "userid": user.username,
            "email": user.email,
            "notify": profile.notify,
            "notify_album": profile.notify_album,
            "notify_single": profile.notify_single,
            "notify_ep": profile.notify_ep,
            "notify_live": profile.notify_live,
            "notify_compilation": profile.notify_compilation,
            "notify_remix": profile.notify_remix,
            "notify_other": profile.notify_other,
        }

    def update(self, request, userid):
        if request.user.username != userid:
            return rc.FORBIDDEN

        user = request.user
        profile = user.profile

        if "email" in request.POST:
            user.email = request.POST["email"].lower().strip()
            profile.email_activated = False
        if "notify" in request.POST:
            profile.notify = request.POST["notify"] in ["1", "true"]
        if "notify_album" in request.POST:
            profile.notify_album = request.POST["notify_album"] in ["1", "true"]
        if "notify_single" in request.POST:
            profile.notify_single = request.POST["notify_single"] in ["1", "true"]
        if "notify_ep" in request.POST:
            profile.notify_ep = request.POST["notify_ep"] in ["1", "true"]
        if "notify_live" in request.POST:
            profile.notify_live = request.POST["notify_live"] in ["1", "true"]
        if "notify_compilation" in request.POST:
            profile.notify_compilation = request.POST["notify_compilation"] in ["1", "true"]
        if "notify_remix" in request.POST:
            profile.notify_remix = request.POST["notify_remix"] in ["1", "true"]
        if "notify_other" in request.POST:
            profile.notify_other = request.POST["notify_other"] in ["1", "true"]

        with transaction.atomic():
            user.save()
            profile.save()

        response = rc.ALL_OK
        response.content = {
            "userid": user.username,
            "email": user.email,
            "notify": profile.notify,
            "notify_album": profile.notify_album,
            "notify_single": profile.notify_single,
            "notify_ep": profile.notify_ep,
            "notify_live": profile.notify_live,
            "notify_compilation": profile.notify_compilation,
            "notify_remix": profile.notify_remix,
            "notify_other": profile.notify_other,
        }
        return response

    def delete(self, request, userid):
        if request.user.username != userid:
            return rc.FORBIDDEN

        request.user.profile.purge()
        return rc.DELETED
