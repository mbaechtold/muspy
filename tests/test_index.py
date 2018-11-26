from unittest.mock import patch

from django_webtest import WebTest
from freezegun import freeze_time
from model_mommy import mommy

from app import models


@patch("app.views.tasks.get_release_groups_by_artist.delay")
@patch("app.views.tasks.update_cover_art_by_mbid.delay")
class TestIndex(WebTest):
    """
    Test the index view.
    """

    def test_index_does_not_show_future_releases(self, *args, **kwargs):
        """
        Test the releases shown on the index view. Future releases must not be shown on the index view.
        """

        # Create the artist we can work with in the test.
        nerf_herder = mommy.make(
            "app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867"
        )

        # Create an album.
        mommy.make(
            "app.ReleaseGroup",
            name="American Cheese",
            mbid="197560f4-2c28-3155-a276-432d8b7aad48",
            date=20020813,
            type="Album",
            artist=nerf_herder,
            is_deleted=False,
        )

        # Create an album having a release date in the future.
        mommy.make(
            "app.ReleaseGroup",
            name="Future Album",
            date=20201231,
            type="Album",
            artist=nerf_herder,
            is_deleted=False,
        )

        # Freeze the time. Unfortunately, the method decorator "@freeze_time()" seems to have no effect.
        freezer = freeze_time("2017-01-01")
        freezer.start()

        # Visit the index view in the browser.
        response = self.app.get("/")
        assert response.status == "200 OK"

        # Albums from the future are not displayed.
        self.assertEqual(
            ["2002-08-13: Nerf Herder \u2013 American Cheese (Album)"],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )

        freezer.stop()

    def test_index_does_not_show_deleted_releases(self, *args, **kwargs):

        # Create the artist we can work with in the test.
        nerf_herder = mommy.make(
            "app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867"
        )

        # Create an album.
        mommy.make(
            "app.ReleaseGroup",
            name="American Cheese",
            mbid="197560f4-2c28-3155-a276-432d8b7aad48",
            date=20020813,
            type="Album",
            artist=nerf_herder,
            is_deleted=False,
        )

        # Create an album having a release date in the future.
        mommy.make(
            "app.ReleaseGroup",
            name="Rockingham",
            mbid="66249588-8b00-4bf1-bfda-9cfc8db5e260",
            date=20160221,
            type="Album",
            artist=nerf_herder,
            is_deleted=True,
        )

        # Visit the index view in the browser.
        response = self.app.get("/")
        assert response.status == "200 OK"

        # Deleted albums are not displayed.
        self.assertEqual(
            ["2002-08-13: Nerf Herder \u2013 American Cheese (Album)"],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )

    def test_index_only_shows_ten_releases(self, *args, **kwargs):
        # Create 11 albums.
        for i in range(11):
            mommy.make("app.ReleaseGroup", name=str(i), date=20001231, is_deleted=False)

        assert models.ReleaseGroup.objects.count() == 11

        # Visit the index view in the browser.
        response = self.app.get("/")
        assert response.status == "200 OK"

        # Deleted albums are not displayed.
        assert len(response.html.find_all("td", "release_info")) == 10
