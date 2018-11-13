from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

# from celery.contrib import rdb
from celery.utils.log import get_task_logger

celery_logger = get_task_logger(__name__)
logger = logging.getLogger("app")


@shared_task()
def check_releases(itze):
    result = str(itze)
    celery_logger.info(f"XXXXXX Result is {result}")
    logger.debug(f"XXXXXX Result is {result}")
    # rdb.set_trace()
    return result


@shared_task()
def foobar():
    result = 42
    celery_logger.info(f"XXXXXX Foobar is {result}")
    logger.debug(f"XXXXXX Foobar is {result}")
    # rdb.set_trace()
    return result
