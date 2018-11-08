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

from configurations import Configuration
from configurations import values
import dj_database_url
import dj_email_url


class Base(Configuration):

    ########################################################################
    # Change the next section in production
    ########################################################################

    DEBUG = True

    SECRET_KEY = values.Value("change me")

    SERVER_EMAIL = 'info@muspy.com'

    email_config = dj_email_url.config(default='smtp://localhost:1025')

    EMAIL_FILE_PATH = email_config['EMAIL_FILE_PATH']
    EMAIL_HOST_USER = email_config['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = email_config['EMAIL_HOST_PASSWORD']
    EMAIL_HOST = email_config['EMAIL_HOST']
    EMAIL_PORT = email_config['EMAIL_PORT']
    EMAIL_BACKEND = email_config['EMAIL_BACKEND']
    EMAIL_USE_TLS = email_config['EMAIL_USE_TLS']
    EMAIL_USE_SSL = email_config['EMAIL_USE_SSL']

    LASTFM_API_KEY = values.Value("change me", environ_prefix="")

    ########################################################################

    ADMINS = (('admin', 'info@muspy.com'),)
    MANAGERS = ADMINS
    SEND_BROKEN_LINK_EMAILS = True

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    DATABASES = {
        'default': dj_database_url.config(default='sqlite:///db/muspy.db')
    }

    TIME_ZONE = None
    USE_I18N = False
    LOGIN_REDIRECT_URL = '/artists'
    LOGIN_URL = '/signin'
    AUTH_PROFILE_MODULE = 'app.UserProfile'
    MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
    ROOT_URLCONF = 'urls'
    EMAIL_SUBJECT_PREFIX = '[muspy] '
    TEMPLATES = [
        {
            "APP_DIRS": True,
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR, "templates")],
            "OPTIONS": {
                "debug": DEBUG,
                "context_processors": [
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.csrf',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                ]
            }
        }
    ]
    AUTHENTICATION_BACKENDS = ('app.backends.EmailAuthBackend',)
    MIDDLEWARE = [
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sites',
        'django_extensions',
        'storages',
        'piston',
        'app',
    ]

    SITE_ID = 1

    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
    ]

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler'
            }
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'django.db': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,  # required to avoid double logging with root logger
            },
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,  # required to avoid double logging with root logger
            },
            'app': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,  # required to avoid double logging with root logger
            },
        },
    }


class SentryMixin(object):
    @property
    def INSTALLED_APPS(self):
        return super(SentryMixin, self).INSTALLED_APPS + ["raven.contrib.django.raven_compat"]

    @property
    def MIDDLEWARE(self):
        return super(SentryMixin, self).MIDDLEWARE + [
            "raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware"
        ]

    # SENTRY_CLIENT = 'raven.contrib.django.raven_compat.DjangoClient'

    SENTRY_DSN = values.Value("", environ_prefix="")

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

    LOGGING = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "verbose": {
                    "format": "%(levelname)s %(asctime)s %(module)s "
                              "%(process)d %(thread)d %(message)s"
                }
            },
            "handlers": {
                "sentry": {
                    "level": "WARNING",  # To capture more than ERROR, change to WARNING, INFO, etc.
                    "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
                    "tags": {"custom-tag": "prod"},
                },
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "verbose",
                },
            },
            "loggers": {
                "root": {"level": "WARNING", "handlers": ["sentry"]},
                "django.db.backends": {
                    "level": "ERROR",
                    "handlers": ["sentry"],
                    "propagate": False,
                },
                "django": {"level": "ERROR", "handlers": ["sentry"], "propagate": False},
                "django.request": {"level": "ERROR", "handlers": ["sentry"], "propagate": True},
                "raven": {"level": "DEBUG", "handlers": ["sentry"], "propagate": False},
                "sentry.errors": {"level": "DEBUG", "handlers": ["sentry"], "propagate": False},
            },
        }


class Production(SentryMixin, Base):

    DEBUG = False

    SECRET_KEY = values.Value(environ_required=True)

    ALLOWED_HOSTS = [
        "muspy.baechtold.me",
        "www.muspy.baechtold.me",
        "muspy.one.baechtold.me",
        "www.muspy.one.baechtold.me",
        "muspy.com",
        "www.muspy.com",
    ]

    AWS_ACCESS_KEY_ID = values.Value("your-spaces-access-key", environ_prefix="")
    AWS_LOCATION = values.Value("your-spaces-files-folder", environ_prefix="")
    AWS_SECRET_ACCESS_KEY = values.Value("your-spaces-secret-access-key", environ_prefix="")
    AWS_STORAGE_BUCKET_NAME = values.Value("your-storage-bucket-name", environ_prefix="")
    
    AWS_S3_ENDPOINT_URL = values.Value("https://ams3.digitaloceanspaces.com", environ_prefix="")
    AWS_S3_REGION_NAME = values.Value("ams3", environ_prefix="")
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }

    STATIC_URL = "https://%s/%s/" % (AWS_S3_ENDPOINT_URL, AWS_LOCATION)
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

