from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q

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
