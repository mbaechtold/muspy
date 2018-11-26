from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import time
from random import randint

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Q
from django.utils.timezone import now

from app import models


celery_logger = get_task_logger(__name__)
logger = logging.getLogger("app")


@shared_task(name="Fetch new releases (periodic task)")
def trigger_release_update_for_outdated_artist():
    """
    This task can be run as a periodic task. It will then trigger an asynchronous check
    for new releases for the artist we checked last.
    """
    artist = models.Artist.objects.all().order_by("last_check_for_releases").first()
    if not artist:
        return "Not checking for new releases because all artists are rather fresh."

    # Make sure the following call implements locking in order not to hammer MusicBrainz.
    get_release_groups_by_artist.delay(artist_mbid=artist.mbid)

    return f"Periodic check for new releases triggered for Artist#{artist.id}."


@shared_task(name="Update cover art (periodic task)")
def update_cover_art():
    release_group_without_cover = (
        models.ReleaseGroup.objects.filter(
            Q(cover_art_url=models.ReleaseGroup.FALLBACK_COVER_ART_URL) | Q(cover_art_url="")
        )
        .order_by("?")
        .first()
    )
    if release_group_without_cover:
        release_group_without_cover.update_cover_art_url()
        return f"Fetching cover art for ReleaseGroup#{release_group_without_cover.id}."
    return "No release group without cover art found."


@shared_task(name="Update cover art of given artist")
def update_cover_art_by_mbid(mbid=None):
    if not mbid:
        return "No mbid provided. Aborting."
    release_group = models.ReleaseGroup.objects.get(mbid=mbid)

    # Wait some time between the checks.
    if release_group.last_check_for_cover_art:
        backoff = 3600 * 7  # Seconds
        seconds_since_last_check = (now() - release_group.last_check_for_cover_art).seconds
        if seconds_since_last_check < backoff:
            return (
                f"Fetching cover art for ReleaseGroup#{release_group.id} is locked. "
                f"Unlocking in {backoff-seconds_since_last_check} seconds."
            )

    # Wait a random amount of seconds so we don't fire too many request at the same time if we have
    # lots of users on the website.
    time.sleep(randint(2, 10))

    release_group.last_check_for_cover_art = now()
    release_group.save()

    release_group.update_cover_art_url()

    return f"Fetching cover art for ReleaseGroup#{release_group.id}."


@shared_task(name="Get release groups of the given artist")
def get_release_groups_by_artist(artist_mbid=None):
    if not artist_mbid:
        return "No mbid provided. Aborting."
    artist = models.Artist.objects.get(mbid=artist_mbid)

    # Wait some time between the checks.
    if artist.last_check_for_releases:
        backoff = 3600 * 7  # Seconds
        seconds_since_last_check = (now() - artist.last_check_for_releases).seconds
        if seconds_since_last_check < backoff:
            return (
                f"Fetching release groups for Artist#{artist.id} is locked. "
                f"Unlocking in {backoff-seconds_since_last_check} seconds."
            )

    artist.last_check_for_releases = now()
    artist.save()

    # Wait a random amount of seconds so we don't fire too many request at the same time if we have
    # lots of users on the website.
    time.sleep(randint(2, 10))

    artist.get_release_groups()

    return f"Fetching release groups for Artist#{artist.id}."


@shared_task(name="Import artists from Last.fm for the given username")
def import_artists_from_lastfm(user_pk, lastfm_username, period, limit):
    user = User.objects.get(pk=user_pk)
    client = settings.LASTFM_CLIENT
    lastfm_user = client.get_user(lastfm_username)
    artists = lastfm_user.get_top_artists(period=period, limit=limit)

    for artist in artists:
        time.sleep(2)
        try:
            mbid = artist.item.get_mbid()
        except:
            continue
        if not mbid:
            continue
        if mbid in models.Artist.blacklisted:
            continue
        artist, created = models.Artist.objects.get_or_create(
            mbid=mbid, defaults={"name": artist[0].name, "sort_name": artist[0].name}
        )
        models.UserArtist.add(user, artist)


@shared_task(name="Notify users")
def notify_user(user_pk, release_group_pk):
    """
    Notify a user about a specific release.
    """
    user = User.objects.get(pk=user_pk)
    release_group = models.ReleaseGroup.objects.get(pk=release_group_pk)
    user.profile.send_email(
        subject="[muspy] New Release: %s - %s" % (release_group.artist.name, release_group.name),
        text_template="email/release.txt",
        html_template="email/release.html",
        release=release_group,
        username=user.username,
        root="https://muspy.baechtold.me/",
    )


@shared_task(name="Get similar artists (periodic task)")
def get_similar_artists():
    """
    This task can be run as a periodic task.
    """

    # Randomly get an artist not having any similar artist.
    # Only update artists having followers.
    artist = (
        models.Artist.objects.annotate(num_similar_artists=Count("similar_artists"))
        .annotate(num_followers=Count("userartist"))
        .filter(num_similar_artists=0, num_followers__gte=1)
        .order_by("?")
        .first()
    )

    if not artist:
        # TODO: The similar artists may change over time. Consider that!
        return f"Every artist has some similar artist(s). Aborting."

    # Wait a random amount of seconds so the requests are not sent too periodically.
    time.sleep(randint(2, 10))

    client = settings.LASTFM_CLIENT
    artist.fetch_similar_artists_from_lastfm(client)

    return f"Fetching similar artists for Artist#{artist.id}."
