from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import time
from random import randint

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils.timezone import now

from app import models


celery_logger = get_task_logger(__name__)
logger = logging.getLogger("app")


@shared_task()
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


@shared_task()
def update_cover_art_by_mbid(mbid=None):
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

    release_group.update_cover_art_url()

    release_group.last_check_for_cover_art = now()
    release_group.save()

    return f"Fetching cover art for ReleaseGroup#{release_group.id}."


@shared_task()
def get_release_groups_by_artist(artist_mbid=None):
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

    # Wait a random amount of seconds so we don't fire too many request at the same time if we have
    # lots of users on the website.
    time.sleep(randint(2, 10))

    artist.get_release_groups()

    artist.last_check_for_releases = now()
    artist.save()

    return f"Fetching release groups for Artist#{artist.id}."
