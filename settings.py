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

import os

import dj_database_url
import dj_email_url
from configurations import Configuration
from configurations import values
from django.contrib import messages

from app.lastfm import get_lastfm_network


class SentryMixin(object):
    SENTRY_DSN = values.Value("", environ_prefix="")

    @property
    def INSTALLED_APPS(self):
        installed_apps = super(SentryMixin, self).INSTALLED_APPS
        if not self.SENTRY_DSN:
            return installed_apps
        return installed_apps + ["raven.contrib.django.raven_compat"]

    @property
    def MIDDLEWARE(self):
        middleware = super(SentryMixin, self).MIDDLEWARE
        if not self.SENTRY_DSN:
            return middleware
        return middleware + [
            "raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware"
        ]

    @property
    def RAVEN_CONFIG(self):
        if not self.SENTRY_DSN:
            return {}
        return {
            "dsn": self.SENTRY_DSN,
            # If you are using git, you can also automatically configure the
            # release based on the git info.
            # TODO: Does not work on Heroku, see https://github.com/getsentry/raven-python/issues/855
            # So probably does not work on Dokku neither.
            # "release": raven.fetch_git_sha(str(super(SentryMixin, self).PROJECT_PATH)),
        }

    @property
    def LOGGING(self):
        logging = super(SentryMixin, self).LOGGING
        if not self.SENTRY_DSN:
            return logging

        # fmt: off
        logging["handlers"]["sentry"] = {
            "level": "DEBUG",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
        }
        logging["loggers"]["raven"] = {
            "level": "ERROR",
            "handlers": ["sentry"],
            "propagate": False,
        }
        logging["loggers"]["sentry.errors"] = {
            "level": "ERROR",
            "handlers": ["sentry"],
            "propagate": False,
        }
        # fmt: on

        return logging


class CeleryMixin:
    @property
    def CELERY_BROKER_URL(self):
        return os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")

    @property
    def INSTALLED_APPS(self):
        installed_apps = super().INSTALLED_APPS
        return installed_apps + ["django_celery_beat"]

    CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    @property
    def CELERY_TIMEZONE(self):
        return super().TIME_ZONE

    CELERY_BEAT_SCHEDULE = {}


class Base(Configuration):

    ########################################################################
    # Change the next section in production
    ########################################################################

    DEBUG = True

    SECRET_KEY = values.Value("change me")

    SERVER_EMAIL = "info@localhost"

    email_config = dj_email_url.config(default="console://localhost:1025")

    EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
    EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
    EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
    EMAIL_HOST = email_config["EMAIL_HOST"]
    EMAIL_PORT = email_config["EMAIL_PORT"]
    EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
    EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
    EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]

    LASTFM_API_KEY = values.Value("change me", environ_prefix="")

    ########################################################################

    ADMINS = (("admin", "info@localhost"),)
    MANAGERS = ADMINS
    SEND_BROKEN_LINK_EMAILS = True

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    DATABASES = {"default": dj_database_url.config(default="sqlite:///db/muspy.db")}

    USE_TZ = True
    TIME_ZONE = "UTC"
    USE_I18N = False
    LOGIN_REDIRECT_URL = "/artists"
    LOGIN_URL = "/signin"
    AUTH_PROFILE_MODULE = "app.UserProfile"
    MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
    ROOT_URLCONF = "urls"
    EMAIL_SUBJECT_PREFIX = "[muspy] "
    TEMPLATES = [
        {
            "APP_DIRS": True,
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR, "templates")],
            "OPTIONS": {
                "debug": DEBUG,
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.csrf",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                ],
            },
        }
    ]
    AUTHENTICATION_BACKENDS = ("app.backends.EmailAuthBackend",)
    MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]

    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.sites",
        "webpack_loader",
        "app.apps.MuspyApp",
        "django_safari_notifications.apps.MuspySafariNotificationsConfig",
    ]

    SITE_ID = 1

    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.SHA1PasswordHasher",
    ]

    WEBPACK_LOADER = {
        "DEFAULT": {
            "CACHE": not DEBUG,
            "BUNDLE_DIR_NAME": "dist/",
            "STATS_FILE": os.path.join(BASE_DIR, "tmp/webpack-stats.json"),
            "POLL_INTERVAL": 0.1,
            "TIMEOUT": None,
            "IGNORE": [".*\.hot-update.js", ".+\.map"],
        }
    }

    # fmt: off
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(process)d %(thread)d --> %(message)s",
            },
            "simple": {
                "format": "%(levelname)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "formatter": "verbose",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.WatchedFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(BASE_DIR, "logs/django.log"),
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "django.db": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,  # required to avoid double logging with root logger
            },
            "django.request": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,  # required to avoid double logging with root logger
            },
            "app": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,  # required to avoid double logging with root logger
            },
        },
    }
    # fmt: on

    @property
    def LASTFM_CLIENT(self):
        return get_lastfm_network(self.BASE_DIR)

    MESSAGE_TAGS = {
        messages.DEBUG: "is-dark",
        messages.INFO: "is-info",
        messages.SUCCESS: "is-success",
        messages.WARNING: "is-warning",
        messages.ERROR: "is-danger",
    }


class Development(CeleryMixin, Base):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    CELERY_BROKER_POOL_LIMIT = 1
    CELERY_BROKER_CONNECTION_TIMEOUT = 10
    CELERY_IGNORE_RESULT = False
    CELERY_TASK_RESULT_EXPIRES = 600


class Production(SentryMixin, CeleryMixin, Base):

    DEBUG = False

    ADMINS = (("admin", "muspy@baechtold.me"),)

    SERVER_EMAIL = "muspy@baechtold.me"

    SECRET_KEY = values.Value(environ_required=True)

    ALLOWED_HOSTS = [
        "muspy.baechtold.me",
        "www.muspy.baechtold.me",
        "muspy.one.baechtold.me",
        "www.muspy.one.baechtold.me",
        "muspy.com",
        "www.muspy.com",
        "localhost",
        "localhost:8000",
    ]

    @property
    def MIDDLEWARE(self):
        middleware = super().MIDDLEWARE
        middleware.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")
        return middleware

    @property
    def LOGGING(self):
        logging = super(Production, self).LOGGING
        if not self.SENTRY_DSN:
            return logging

        # fmt: off
        logging["loggers"] = {
            "": {
                "handlers": ["sentry"],
                "level": "ERROR",
            },
            "django.db": {
                "handlers": ["sentry"],
                "level": "WARNING",
                "propagate": False,  # required to avoid double logging with root logger
            },
            "django.request": {
                "handlers": ["sentry"],
                "level": "WARNING",
                "propagate": False,  # required to avoid double logging with root logger
            },
            "app": {
                "handlers": ["sentry"],
                "level": "WARNING",
                "propagate": False,  # required to avoid double logging with root logger
            },
        }
        # fmt: on
        return logging

    @property
    def WEBPACK_LOADER(self):
        config = super().WEBPACK_LOADER
        config["DEFAULT"]["STATS_FILE"] = os.path.join(self.BASE_DIR, "tmp/webpack-stats-prod.json")
        return config
