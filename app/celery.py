from __future__ import absolute_import, unicode_literals

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

# Read environment variables from the files in the directory "./.env_vars/".
current_folder = os.path.dirname(os.path.abspath(__file__))
envdir_folder = os.path.join(os.path.dirname(current_folder), ".env_vars")
if os.path.exists(envdir_folder):
    import envdir

    envdir.open(envdir_folder)

# TODO: Look into https://github.com/jazzband/django-configurations/issues/196
from configurations import importer

importer.install()

from celery import Celery

app = Celery("muspy")

# Using a string here means the worker doesn't have to serialize the configuration object to child processes.
# namespace='CELERY' means all celery-related configuration keys should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
from django.conf import settings

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
