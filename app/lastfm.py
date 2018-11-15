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
import re
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen
from xml.etree import ElementTree as et

import pylast
from django.conf import settings


def has_user(username):
    return get_artists(username, "overall", 1, 1) != None


def get_artists(username, period, limit, page):
    try:
        xml = _fetch("user.getTopArtists", user=username, period=period, limit=limit, page=page)
    except:
        return None

    try:
        root = et.fromstring(xml)
    except:
        return []

    if not "status" in root.attrib or root.get("status") != "ok":
        return None

    artists = root.find("topartists")
    if artists is None or int(artists.get("page")) != page:
        return []

    artists = [_parse_artist(element) for element in root.findall("topartists/artist")]
    return [artist for artist in artists if "name" in artist or "mbid" in artist]


def get_cover_urls(artist, album):
    # Remove the trailing ' (X)' from the album.
    album = re.sub(r"(^.+)\s+\([^\)]+\)$", r"\1", album)
    try:
        xml = _fetch("album.getInfo", artist=artist, album=album)
    except:
        return None

    pattern = r'<image size="%s">(?P<url>[^<]+)</image>'
    res = []
    for size in ("large", "extralarge", "mega"):
        match = re.search(pattern % size, xml)
        if match:
            res.append(match.group("url"))

    return res


def _fetch(method, **kw):
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": method, "api_key": settings.LASTFM_API_KEY}
    params.update(kw)
    url += "?" + urlencode(params)

    request = Request(url, headers={"User-Agent": "muspy/2.0"})
    response = urlopen(request)
    return response.read().decode()


def _parse_artist(element):
    d = {}
    for prop in element.getchildren():
        if prop.tag in ("name", "mbid"):
            d[prop.tag] = prop.text
    return d


def get_lastfm_network():
    """
    Please don't use this directly. You can get the singleton Last.fm client from the
    Django settings:

        from django.conf import settings
        client = settings.LASTFM_CLIENT
    """

    return pylast.LastFMNetwork(
        api_key=os.environ.get("LASTFM_API_KEY", ""),
        api_secret=os.environ.get("LASTFM_API_SECRET", ""),
        username=os.environ.get("LASTFM_USERNAME", ""),
        password_hash=pylast.md5(os.environ.get("LASTFM_PASSWORD", "")),
    )
