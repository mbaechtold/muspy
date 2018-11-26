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

import logging
from calendar import monthrange
from datetime import date
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django_ical.views import ICalFeed
from pylast import PERIOD_3MONTHS
from pylast import PERIOD_6MONTHS
from pylast import PERIOD_7DAYS
from pylast import PERIOD_12MONTHS
from pylast import PERIOD_OVERALL

from app import lastfm
from app.cover import Cover
from app.forms import *
from app.models import *
from app.tools import arrange_for_table


logger = logging.getLogger("app")


def activate(request):
    if "code" in request.GET:
        if UserProfile.activate(request.GET["code"]):
            messages.success(request, "Your email address has been activated.")
        else:
            messages.error(
                request, "Invalid activation code, your email address was not activated."
            )
        return redirect("/")

    if not request.user.is_authenticated:
        messages.error(request, "You need to sign in to activate your email address.")
        return redirect("/")

    if request.user.profile.email_activated:
        messages.info(request, "Your email address is already active.")
        return redirect("/")

    request.user.profile.send_activation_email(request)
    return render(request, "activate.html")


def artist(request, mbid):
    try:
        artist = Artist.get_by_mbid(mbid)
    except (Artist.Blacklisted, Artist.Unknown):
        return HttpResponseNotFound()
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    # The user triggers a potential query for new release groups.
    tasks.get_release_groups_by_artist.delay(artist_mbid=artist.mbid)

    user_has_artist = request.user.is_authenticated and UserArtist.get(request.user, artist)
    if user_has_artist:
        show_stars = True
        queryset = ReleaseGroup.get(artist=artist, user=request.user)
    else:
        show_stars = False
        queryset = ReleaseGroup.get(artist=artist)

    release_groups = queryset.all()

    page = request.GET.get("page")
    page_size = 10
    paginator = Paginator(release_groups, page_size)

    release_groups_current_page = paginator.get_page(page)

    for release_group in release_groups_current_page:
        # The user triggers a potential query for a newer cover art for the release groups.
        tasks.update_cover_art_by_mbid.delay(release_group.mbid)

    recommended_artists = []
    if request.user.is_authenticated:
        user_artists = [user_artist.artist for user_artist in request.user.favorite_artists.all()]
        recommended_artists = [
            artist for artist in artist.similar_artists.all() if artist not in user_artists
        ][:10]

    return render(
        request,
        "artist.html",
        {
            "artist": artist,
            "release_groups": release_groups_current_page,
            "page": page,
            "paginator": paginator,
            "user_has_artist": user_has_artist,
            "show_stars": show_stars,
            "recommended_artists": recommended_artists,
        },
    )


@login_required
def artists(request):
    artists = Artist.get_by_user(request.user)

    COLUMNS = 3
    artist_rows = arrange_for_table(artists, COLUMNS)

    # Using REQUEST because this handler can be called using both GET and POST.
    search = request.POST.get("search", "")
    dontadd = request.POST.get("dontadd", "")
    offset = request.POST.get("offset", "")
    offset = int(offset) if offset.isdigit() else 0

    found_artists, count = [], 0
    LIMIT = 20
    if search:
        if len(search) > 16384:
            messages.error(request, "The search string is too long.")
            return redirect("/artists")

        # FB likes are separated by '*'. 32 is completely random.
        if len(search) > 32 and search.count("*") > len(search) // 32:
            searches = [s.strip() for s in search.split("*") if s.strip()]
        else:
            searches = [s.strip() for s in search.split(",") if s.strip()]
        if len(searches) > 1 and not offset:
            # Batch add mode.
            if dontadd:
                messages.warning(
                    request,
                    "Cannot search for multiple artists. "
                    "Remove all commas and asterisks to search.",
                )
                return render(
                    request,
                    "artists.html",
                    {"artist_rows": artist_rows, "search": search, "dontadd": dontadd},
                )

            Job.add_artists(request.user, searches)
            messages.info(
                request,
                "Your artists will be processed in the next couple of "
                "minutes. In the meantime you can add more artists.",
            )
            return redirect("/artists")

        found_artists, count = mb.search_artists(search, limit=LIMIT, offset=offset)
        if found_artists is None:
            messages.error(
                request,
                "The search server could not fulfil your request "
                "due to an internal error. Please try again later.",
            )
            return render(
                request,
                "artists.html",
                {"artist_rows": artist_rows, "search": search, "dontadd": dontadd},
            )

        only_one = len(found_artists) == 1
        first_is_exact = (
            len(found_artists) > 1
            and found_artists[0]["name"].lower() == search.lower()
            and found_artists[1]["name"].lower() != search.lower()
        )
        if not dontadd and not offset and (only_one or first_is_exact):
            # Only one artist found - add it right away.
            artist_data = found_artists[0]
            mbid = artist_data["id"]
            try:
                artist = Artist.get_by_mbid(mbid)
            except (Artist.Blacklisted, Artist.Unknown):
                return redirect("/artists")
            if not artist:
                # TODO: error message
                return redirect("/artists")

            UserArtist.add(request.user, artist)
            messages.success(request, "%s has been added!" % artist.name)
            return redirect("/artists")

    artists_offset = offset + len(found_artists)
    artists_left = max(0, count - artists_offset)
    found_artists = [a for a in found_artists if a["id"] not in Artist.blacklisted]

    importing = ", ".join(Job.importing_artists(request.user))

    pending = sorted(s.search for s in UserSearch.get(request.user)[:200])
    pending_rows = arrange_for_table(pending, COLUMNS)

    return render(
        request,
        "artists.html",
        {
            "artist_rows": artist_rows,
            "artist_count": len(artists),
            "search": search,
            "dontadd": dontadd,
            "found_artists": found_artists,
            "artists_offset": artists_offset,
            "artists_left": artists_left,
            "importing": importing,
            "pending_rows": pending_rows,
            "pending_count": len(pending),
            # TODO: Improve the algorithm. Users should also be able to ignore the recommendations.
            # "recommended_artists": request.user.profile.get_recommended_artists()[:20],
        },
    )


@login_required
def artists_add(request):
    mbid = request.GET.get("id", "").lower()
    try:
        artist = Artist.get_by_mbid(mbid)
    except Artist.Blacklisted:
        messages.error(request, "The artist is special-purpose and cannot be added")
        return redirect("/artists")
    except Artist.Unknown:
        messages.error(request, "Unknown artist")
        return redirect("/artists")
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    UserArtist.add(request.user, artist)

    search = request.GET.get("search", "")
    UserSearch.remove(request.user, [search])

    messages.success(request, "%s has been added!" % artist.name)
    return redirect("/artists")


@login_required
def artists_remove(request):
    names = request.POST.getlist("name")
    mbids = request.POST.getlist("id")
    if not names and not mbids:
        messages.info(request, "Use checkboxes to select the artists you want to remove.")
        return redirect("/artists")

    if names:
        UserSearch.remove(request.user, names)
        messages.success(request, "Removed %d pending artists." % len(names))
        return redirect("/artists")

    UserArtist.remove(request.user, mbids)
    messages.success(request, "Removed %d artist%s." % (len(mbids), "s" if len(mbids) > 1 else ""))
    return redirect("/artists")


@cache_control(max_age=24 * 60 * 60)
def cover(request):
    mbid = request.GET.get("id", "")
    cover = Cover(mbid)
    if not cover.found:
        Job.get_cover(mbid)
        return HttpResponseNotFound(content=cover.image, content_type="image/jpeg")
    return HttpResponse(content=cover.image, content_type="image/jpeg")


@login_required
def delete(request):
    if request.POST.get("confirm", "") == "1":
        profile = request.user.profile
        logout(request)
        profile.purge()
        return redirect("/")

    return render(request, "delete.html")


def feed(request):
    user_id = request.GET.get("id", "")
    if user_id.isdigit():
        profile = UserProfile.get_by_legacy_id(user_id)
        if profile:
            return redirect("/feed?id=" + profile.user.username, permanent=True)

    profile = UserProfile.get_by_username(user_id)
    if not profile:
        return HttpResponseNotFound()

    LIMIT = 40
    releases = ReleaseGroup.get(user=profile.user, feed=True)[:LIMIT]
    date_iso8601 = None
    if releases:
        date_iso8601 = max(r.date_iso8601() for r in releases)

    return render(
        request,
        "feed.xml",
        {
            "releases": releases,
            "date_iso8601": date_iso8601,
            "url": request.build_absolute_uri(),
            "root": request.build_absolute_uri("/"),
        },
        content_type="application/atom+xml",
    )


def ical_redirect(request):
    username = request.GET.get("id", "")
    return redirect("ical", username)


class MuspyFeed(ICalFeed):
    timezone = settings.TIME_ZONE
    filename = "muspy.ics"
    limit = 40

    def __call__(self, request, *args, **kwargs):
        self.request = request
        self.profile = UserProfile.get_by_username(kwargs.pop("username"))
        self.hostname = urlsplit(self.request.build_absolute_uri("/")).netloc
        if not self.profile:
            return HttpResponseNotFound()
        return super(MuspyFeed, self).__call__(request, *args, **kwargs)

    @property
    def product_id(self):
        return f"-//{self.hostname}//1.0//EN"

    def title(self):
        return "Muspy"

    def items(self):
        items = []
        queryset = ReleaseGroup.get(user=self.profile.user, feed=True)[: self.limit]
        for release_group in queryset:
            # month/day aren't always present.
            month = (release_group.date // 100) % 100
            if month == 0:
                continue
            items.append(release_group)
        return items

    def item_title(self, item):
        return f"{item.artist.name} - {item.name}"

    def item_description(self, item):
        day = item.date % 100
        if day == 0:
            return "The exact release date is subject to change."
        return ""

    def item_start_datetime(self, item):
        year = item.date // 10000
        month = (item.date // 100) % 100
        day = item.date % 100
        if day == 0:
            # arbitrarily set the release as the last day of the month.
            # hopefully, the date will be clarified before then, but this
            # will ensure it's not missed on the calendar.
            day = monthrange(year, month)[1]
        return date(year, month, day)

    def item_end_datetime(self, item):
        return self.item_start_datetime(item) + timedelta(days=1)

    def item_guid(self, item):
        return f"{str(item.id)}@{self.hostname}"

    def item_link(self, item):
        return item.artist.get_absolute_url()


def forbidden(request):
    return HttpResponseForbidden()


@login_required
def import_artists(request):
    if request.method == "GET":
        return render(request, "import.html")

    type = request.POST.get("type", "")
    if type == "last.fm":
        username = request.POST.get("username", "")
        if not username:
            messages.error(request, "Please enter your Last.fm user name.")
            return redirect("/import")

        if not lastfm.has_user(username):
            messages.error(request, "Unknown user: %s" % username)
            return redirect("/import")

        count = request.POST.get("count", "")
        count = int(count) if count.isdigit() else 50
        count = min(500, count)
        period = request.POST.get("period", "")
        if period not in [
            PERIOD_OVERALL,
            PERIOD_12MONTHS,
            PERIOD_6MONTHS,
            PERIOD_3MONTHS,
            PERIOD_7DAYS,
        ]:
            period = PERIOD_OVERALL

        tasks.import_artists_from_lastfm.delay(
            user_pk=request.user.pk, lastfm_username=username, period=period, limit=count
        )

        messages.info(
            request,
            "Your artists will be imported in a few minutes. "
            "Refresh this page to track the progress of the import.",
        )
        return redirect("/artists")

    return redirect("/import")


def index(request):
    today = int(date.today().strftime("%Y%m%d"))
    releases = ReleaseGroup.get_calendar(today, 10, 0)
    return render(request, "index.html", {"is_index": True, "releases": releases})


@login_required
def releases(request):
    queryset = ReleaseGroup.get(user=request.user)

    release_groups = queryset.all()

    page = request.GET.get("page")
    page_size = 10
    paginator = Paginator(release_groups, page_size)

    release_groups_current_page = paginator.get_page(page)

    return render(
        request,
        "releases.html",
        {
            "release_groups": release_groups_current_page,
            "page": page,
            "page_size": page_size,
            "paginator": paginator,
            "show_stars": True,
        },
    )


def reset(request):
    form = code = user = None
    if request.method == "POST":
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            profile = UserProfile.get_by_email(email)
            if not profile:
                # TODO: Remove. This will never happen because the form validation already checked for user profile and raise a validation error.
                messages.error(request, "Unknown email address: " + email)
                return redirect("/")
            profile.send_reset_email(request)
            messages.success(
                request,
                "An email has been sent to %s describing how to "
                "obtain your new password." % email,
            )
            return redirect("/")
    elif "code" in request.GET:
        code = request.GET["code"]
        email, password = UserProfile.reset(code)
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                login(request, user)
                return redirect("/settings")
    else:
        form = ResetForm()

    return render(request, "reset.html", {"form": form, "code": code, "user": user})


@login_required
def settings(request):
    if request.method == "POST":
        form = SettingsForm(data=request.POST, request=request)
        form.profile = request.user.profile
        if form.is_valid():
            form.save()
            messages.success(request, "Your settings have been saved.")
            return redirect(request.path)
    else:
        initial = {
            "email": request.user.email,
            "notify": request.user.profile.notify,
            "notify_album": request.user.profile.notify_album,
            "notify_single": request.user.profile.notify_single,
            "notify_ep": request.user.profile.notify_ep,
            "notify_live": request.user.profile.notify_live,
            "notify_compilation": request.user.profile.notify_compilation,
            "notify_remix": request.user.profile.notify_remix,
            "notify_other": request.user.profile.notify_other,
        }
        form = SettingsForm(initial=initial, request=request)

    return render(request, "settings.html", {"form": form})


def signup(request):
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        form.save(request)
        user = authenticate(
            username=form.cleaned_data["email"], password=form.cleaned_data["password"]
        )
        user.profile.send_activation_email(request)
        login(request, user)
        return redirect(django_settings.LOGIN_REDIRECT_URL)

    return render(request, "signup.html", {"form": form})


@login_required
def signout(request):
    logout(request)
    return redirect("/")


def sitemap(request):
    root = request.build_absolute_uri("/")
    return render(request, "sitemap.xml", {"root": root}, content_type="text/xml")


@login_required
def star(request):
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER", "/"))
    id = request.POST.get("id", 0).lower()
    value = int(request.POST.get("value", 0))
    Star.set(request.user, id, value)
    return HttpResponse("{}", "application/json")


def unsubscribe(request):
    username = request.GET.get("id", "")
    profile = UserProfile.get_by_username(username) if username else None
    if not profile:
        messages.error(request, "Bad request, you were not unsubscribed.")
        return redirect("/")
    profile.unsubscribe()
    messages.success(
        request,
        "You have successfully unsubscribed from release notifications. "
        "If you change your mind, you can subscribe to notifications on the Settings page.",
    )
    return redirect("/")
