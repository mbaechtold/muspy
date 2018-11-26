from django_webtest import WebTest

from app import models


class TestArtists(WebTest):
    """
    Test the artists view.

    # TODO: We need to mock the LastFM API calls so we don't hit LastFM during the tests.
    """

    csrf_checks = False

    def test_with_anonymous_user(self):
        response = self.app.get("/artists", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/artists"

    def test_with_user(self):
        # The user searches an artist.
        response = self.app.post("/artists", {"search": "Nerf Herder"}, user="john.doe")

        # A redirect happens.
        assert response.status == "302 Found"
        assert response.url == "/artists"

        # Follow the redirect.
        response = response.follow()
        assert response.status == "200 OK"
        self.assertEqual(
            "Nerf Herder has been added!", response.html.find("div", "message success").text.strip()
        )

        # The artist has been created.
        assert models.Artist.objects.count() == 1
        artist = models.Artist.objects.first()
        assert artist.name == "Nerf Herder"

        # The user now follows the artist he just added.
        user = response.context["user"]
        assert user.favorite_artists.first().artist.name == "Nerf Herder"
