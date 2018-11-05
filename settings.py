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

########################################################################
# Change the next section in production
########################################################################

DEBUG = True

SECRET_KEY = 'change me'

SERVER_EMAIL = 'info@muspy.com'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

LASTFM_API_KEY='change me'

########################################################################

ADMINS = (('admin', 'info@muspy.com'),)
MANAGERS = ADMINS
SEND_BROKEN_LINK_EMAILS = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db/muspy.db',
        'OPTIONS': { 'timeout': 20 },
    }
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
        }
    }
]
AUTHENTICATION_BACKENDS = ('app.backends.EmailAuthBackend',)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MIDDLEWARE_CLASSES = (
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
    'piston',
    'app',
)

SITE_ID = 1

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

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
