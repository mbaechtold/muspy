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

from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView

from app import views
from app.forms import SignInForm


urlpatterns = [
    url(r"^$", views.index),
    url(r"^activate$", views.activate),
    url(r"^about$", TemplateView.as_view(template_name="about.html")),
    url(r"^artist/([0-9a-f\-]+)$", views.artist, name="artist"),
    url(r"^artists$", views.artists),
    url(r"^artists-add$", views.artists_add),
    url(r"^artists-remove$", views.artists_remove),
    url(r"^blog$", RedirectView.as_view(url="http://kojevnikov.com/tag/muspy.html")),
    url(r"^blog/feed$", RedirectView.as_view(url="http://kojevnikov.com/muspy.xml")),
    url(r"^contact$", TemplateView.as_view(template_name="contact.html")),
    url(r"^cover$", views.cover),
    url(r"^delete$", views.delete),
    url(r"^faq$", TemplateView.as_view(template_name="faq.html")),
    url(r"^feed$", views.feed),
    url(r"^feed/(?P<id>\d+)$", RedirectView.as_view(url="/feed?id=%(id)s")),
    url(r"^ical$", views.ical),
    url(r"^import$", views.import_artists),
    url(r"^releases$", views.releases),
    url(r"^reset$", views.reset),
    url(r"^settings$", views.settings),
    url(
        r"^signin$", LoginView.as_view(authentication_form=SignInForm, template_name="signin.html")
    ),
    url(r"^signout$", views.signout),
    url(r"^signup$", views.signup),
    url(r"^sitemap.xml$", views.sitemap),
    url(r"^star$", views.star),
    url(r"^unsubscribe$", views.unsubscribe),
    url(r"blog|\.php", views.forbidden),  # Hello, vulnerability scan bots!
]

admin_url_path = os.environ.get("DJANGO_ADMIN_URL")
if admin_url_path:
    # Ensure a trailing slash.
    admin_url_path = admin_url_path.strip("/") + "/"
    urlpatterns += [path(admin_url_path, admin.site.urls)]


# "django-piston" relies on "django.utils.simplejson", which has been removed in Django 1.5.
# Since it's no longer maintained, the API will have to be rewritten entirely.
# urlpatterns += patterns('',
#     (r'^api/1/', include('api.urls')),
# )
