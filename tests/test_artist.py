from django_webtest import WebTest
from freezegun import freeze_time
from model_mommy import mommy


class TestArtist(WebTest):
    """
    Test the artist detail view.
    """

    def test_non_existing_artist(self):
        """
        The artist view also renders future releases.
        """
        response = self.app.get("/artist/000-0000-000", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_index_shows_future_releases(self):
        """
        The artist view also renders future releases.
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

        # Visit the artist view in the browser.
        response = self.app.get("/artist/{}".format(nerf_herder.mbid))
        assert response.status == "200 OK"

        # Albums from the future are not displayed.
        self.assertEqual(
            [
                u"2020-12-31: Nerf Herder \u2013 Future Album (Album)",
                u"2002-08-13: Nerf Herder \u2013 American Cheese (Album)",
            ],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )

        freezer.stop()

    def test_blacklisted_artist(self):
        blacklisted_artist = mommy.make("app.Artist", mbid="89ad4ac3-39f7-470e-963a-56509c546377")
        response = self.app.get("/artist/{}".format(blacklisted_artist.mbid), expect_errors=True)
        assert response.status == "404 Not Found"

    def test_invalid_offset(self):
        nerf_herder = mommy.make(
            "app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867"
        )
        response = self.app.get(
            "/artist/{}?offset=boom".format(nerf_herder.mbid), expect_errors=True
        )
        assert response.status == "404 Not Found"
