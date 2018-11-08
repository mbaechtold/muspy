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
    MIDDLEWARE = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    )

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sites',
        'django_extensions',
        'piston',
        'app',
    )

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
