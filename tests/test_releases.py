from django_webtest import WebTest
from model_mommy import mommy

from app import models


class TestReleases(WebTest):
    """
    Test the releases view.
    """

    def test_with_anonymous_user(self):
        response = self.app.get("/releases", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/releases"

    def test_show_releases_of_the_artists_a_user_follows(self):
        # Create a user we can work with in the test.
        john = mommy.make("User", username="john.doe")

        # Create the artist "Nerf Herder" and a release.
        nerf_herder = mommy.make("app.Artist", name="Nerf Herder")
        mommy.make(
            "app.ReleaseGroup",
            artist=nerf_herder,
            name="Rockingham",
            type="Album",
            is_deleted=False,
            date=20160221,
        )

        # John follows "Nerf Herder".
        mommy.make("app.UserArtist", user=john, artist=nerf_herder)

        # Create another artist having an album. Note how john does not follow this artist..
        foo_fighters = mommy.make("app.Artist", name="Foo Fighters")
        mommy.make(
            "app.ReleaseGroup",
            artist=foo_fighters,
            name="In Your Honor",
            type="Album",
            is_deleted=False,
            date=20160221,
        )

        # Visit the releases view in the browser.
        response = self.app.get("/releases", user=john)
        assert response.status == "200 OK"

        # Only the albums from followed artists are shown.
        self.assertEqual(
            ["2016-02-21: Nerf Herder \u2013 Rockingham (Album)"],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )

    def test_starred_releases_on_top(self):
        # Create a user we can work with in the test.
        john = mommy.make("User", username="john.doe")

        # Create the artist "Nerf Herder" and 3 (fake) releases.
        nerf_herder = mommy.make("app.Artist", name="Nerf Herder")
        for i in range(1, 4):
            mommy.make(
                "app.ReleaseGroup",
                id=i,
                artist=nerf_herder,
                name="Album #{}".format(str(i)),
                type="Album",
                is_deleted=False,
                date=20001201 + i,
            )

        # John follows Nerf Herder.
        mommy.make("app.UserArtist", user=john, artist=nerf_herder)

        # John opens the releases view in the browser.
        response = self.app.get("/releases", user=john)
        assert response.status == "200 OK"

        # The albums are sorted by release date (in descending order).
        self.assertEqual(
            [
                "2000-12-04: Nerf Herder \u2013 Album #3 (Album)",
                "2000-12-03: Nerf Herder \u2013 Album #2 (Album)",
                "2000-12-02: Nerf Herder \u2013 Album #1 (Album)",
            ],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )

        # John stars the oldest albums.
        mommy.make("app.Star", user=john, release_group=models.ReleaseGroup.objects.get(id=1))

        # John refreshes the releases view in the browser.
        response = self.app.get("/releases", user=john)
        assert response.status == "200 OK"

        # The starred album is shown at the top.
        self.assertEqual(
            [
                "2000-12-02: Nerf Herder \u2013 Album #1 (Album)",
                "2000-12-04: Nerf Herder \u2013 Album #3 (Album)",
                "2000-12-03: Nerf Herder \u2013 Album #2 (Album)",
            ],
            [node.text.strip() for node in response.html.find_all("td", "release_info")],
        )
