# -*- coding: utf-8 -*-
#
# Copyright © 2009-2012 Alexander Kojevnikov <alexander@kojevnikov.com>
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

import datetime
import logging

from app.models import *
from app.tools import str_to_date
from daemon import jobs
from daemon import notifications
from daemon import tools


def check():
    logging.info("Start checking artists")
    sent_notifications = 0
    checked_artists = 0
    checked_release_groups = 0
    day = datetime.datetime.utcnow().day
    artist = None
    while True:

        # Get the next artist.
        artists = Artist.objects.order_by("mbid")
        if artist:
            artists = artists.filter(mbid__gt=artist.mbid)
        try:
            artist = artists[0]
        except IndexError:
            break  # last artist

        checked_artists += 1

        # Artist names don't change that often. Update artists at most 3 times
        # a month, unless we are debugging.
        if settings.DEBUG or day in (1, 11, 21):
            jobs.process()
            tools.sleep()
            logging.info("Updating artist %s" % artist.mbid)
            artist_data = mb.get_artist(artist.mbid)
            if not artist_data:
                # TODO: musicbrainz/network error or deleted?
                logging.warning("Could not fetch artist data")
            elif artist_data["id"] != artist.mbid:
                # Requested and returned mbids are different if the artist has been merged.
                logging.info("Merging into artist %s" % artist_data["id"])
                try:
                    new_artist = Artist.get_by_mbid(artist_data["id"])
                except (Artist.Blacklisted, Artist.Unknown):
                    continue
                if not new_artist:
                    continue
                cursor = connection.cursor()
                cursor.execute(
                    """
                    UPDATE OR REPLACE "app_userartist"
                    SET "artist_id" = %s
                    WHERE "artist_id" = %s
                    """,
                    [new_artist.id, artist.id],
                )
                # Delete the artist and its release groups.
                # Use SQL, delete() is buggy, see Django bug #16426.
                # TODO: possible FK constraint fail in app_star.
                cursor.execute(
                    """
                    DELETE FROM "app_releasegroup"
                    WHERE "artist_id" = %s
                    """,
                    [artist.id],
                )
                logging.info("Deleted release groups")
                cursor.execute(
                    """
                    DELETE FROM "app_artist"
                    WHERE "id" = %s
                    """,
                    [artist.id],
                )
                logging.info("Deleted the artist")
                continue
            else:
                # Update artist info if changed.
                updated = False
                if artist.name != artist_data["name"]:
                    artist.name = artist_data["name"]
                    updated = True
                if artist.sort_name != artist_data["sort-name"]:
                    artist.sort_name = artist_data["sort-name"]
                    updated = True
                if artist.disambiguation != artist_data.get("disambiguation", ""):
                    artist.disambiguation = artist_data.get("disambiguation", "")
                    updated = True
                if updated:
                    logging.info("Artist changed, updating")
                    artist.save()
        else:
            logging.info("Checking artist %s" % artist.mbid)

        current = {rg.mbid: rg for rg in ReleaseGroup.objects.filter(artist=artist)}

        # Get release groups
        LIMIT = 100
        offset = 0
        while True:
            sent_notifications += notifications.send()
            release_groups = mb.get_release_groups(artist.mbid, LIMIT, offset)
            if release_groups is None:
                logging.warning("Could not fetch release groups, retrying")
                continue
            logging.info("Fetched %s release groups" % len(release_groups))
            with transaction.atomic():
                for rg_data in release_groups:
                    mbid = rg_data["id"]
                    # Ignore releases without a release date or a type.
                    release_date = str_to_date(rg_data.get("first-release-date"))
                    if not release_date or not rg_data.get("type"):
                        if mbid in current:
                            release_group = current[mbid]
                            if not release_group.is_deleted:
                                release_group.is_deleted = True
                                release_group.save()
                                logging.info("Deleted release group %s" % mbid)
                        continue

                    checked_release_groups += 1
                    if mbid in current:
                        release_group = current[mbid]

                        updated = False
                        if release_group.is_deleted:
                            release_group.is_deleted = False
                            updated = True
                        # Work-around MBS-4285.
                        if release_group.name != rg_data["title"] and rg_data["title"]:
                            release_group.name = rg_data["title"]
                            updated = True
                        if release_group.type != rg_data["type"]:
                            release_group.type = rg_data["type"]
                            updated = True
                        if release_group.date != release_date:
                            release_group.date = release_date
                            updated = True
                        if updated:
                            release_group.save()
                            logging.info("Updated release group %s" % mbid)

                        del current[mbid]
                    elif rg_data["title"]:
                        release_group = ReleaseGroup(
                            artist=artist,
                            mbid=rg_data["id"],
                            name=rg_data["title"],
                            type=rg_data["type"],
                            date=release_date,
                            is_deleted=False,
                        )
                        release_group.save()
                        logging.info("Created release group %s" % mbid)

                        # Notify users
                        cursor = connection.cursor()
                        cursor.execute(
                            """
                            INSERT INTO "app_notification" ("user_id", "release_group_id")
                            SELECT "app_userartist"."user_id", "app_releasegroup"."id"
                            FROM "app_userartist"
                            JOIN "app_artist" ON "app_artist"."id" = "app_userartist"."artist_id"
                            JOIN "app_releasegroup" ON "app_releasegroup"."artist_id" = "app_artist"."id"
                            WHERE "app_releasegroup"."id" = %s
                            """,
                            [release_group.id],
                        )
                        logging.info("Will notify %d users" % cursor.rowcount)

            if len(release_groups) < LIMIT:
                break
            offset += LIMIT

        with transaction.atomic():
            for mbid in current:
                release_group = current[mbid]
                if not release_group.is_deleted:
                    release_group.is_deleted = True
                    release_group.save()
                    logging.info("Deleted release group %s" % mbid)

    return (checked_artists, checked_release_groups, sent_notifications)
