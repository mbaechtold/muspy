from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when Django starts
# so that shared_task will use this app.
from .celery import app as muspy

# Make the imported Celery app public to this package.
# This way we can start the Celery worker by setting the application to this package:
#
#    celery --app=app worker
#
__all__ = ['muspy']
