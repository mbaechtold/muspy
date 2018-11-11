from django_webtest import WebTest
from freezegun import freeze_time
from model_mommy import mommy

from app import models
from daemon import releases


class TestDaemon(WebTest):
    """
    Test the "artists remove" view.

    # TODO: We need to mock the LastFM API calls so we don't hit LastFM during the tests.
    """

    def test_daemon(self):
        mommy.make("app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867")

        # Freeze the time, because some checks are only executed at a specific day of the month.
        # Unfortunately, the method decorator "@freeze_time()" seems to have no effect.
        freezer = freeze_time("2017-01-01")
        freezer.start()

        releases.check()

        freezer.stop()

    def test_add_artist_job(self):
        mommy.make(
            "app.Job", type=models.Job.ADD_ARTIST, data="da66103a-1307-400d-8261-89d856126867"
        )

        # Freeze the time, because some checks are only executed at a specific day of the month.
        # Unfortunately, the method decorator "@freeze_time()" seems to have no effect.
        freezer = freeze_time("2017-01-01")
        freezer.start()

        releases.check()

        freezer.stop()

    def test_add_add_release_group_job(self):
        mommy.make("app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867")
        mommy.make(
            "app.Job",
            type=models.Job.ADD_RELEASE_GROUPS,
            data="da66103a-1307-400d-8261-89d856126867",
        )

        # Freeze the time, because some checks are only executed at a specific day of the month.
        # Unfortunately, the method decorator "@freeze_time()" seems to have no effect.
        freezer = freeze_time("2017-01-01")
        freezer.start()

        releases.check()

        freezer.stop()

    def test_get_cover_job(self):
        mommy.make("app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867")
        mommy.make(
            "app.Job", type=models.Job.GET_COVER, data="4824ab74-167e-48db-abb1-8e31088331ba"
        )

        # Freeze the time, because some checks are only executed at a specific day of the month.
        # Unfortunately, the method decorator "@freeze_time()" seems to have no effect.
        freezer = freeze_time("2017-01-01")
        freezer.start()

        releases.check()

        freezer.stop()
