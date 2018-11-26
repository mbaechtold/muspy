from django_webtest import WebTest
from model_mommy import mommy


class TestArtistsRemove(WebTest):
    """
    Test the "artists remove" view.
    """

    csrf_checks = False

    def test_with_anonymous_user(self):
        response = self.app.get("/artists-remove", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/artists-remove"

        response = self.app.post("/artists-remove", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/artists-remove"

    def test_no_artist_submitted(self):
        john = mommy.make("User", username="john.doe")
        john.profile.email_activated = True
        john.profile.notify = True
        john.profile.save()

        response = self.app.get("/artists-remove", user="john.doe")
        assert response.status == "302 Found"
        assert response.url == "/artists"

        response = response.follow()

        self.assertEqual(
            "Use checkboxes to select the artists you want to remove.",
            response.html.find("div", "message info").text.strip(),
        )

        response = self.app.post("/artists-remove", user="john.doe")
        assert response.status == "302 Found"
        assert response.url == "/artists"

        response = response.follow()

        self.assertEqual(
            "Use checkboxes to select the artists you want to remove.",
            response.html.find("div", "message info").text.strip(),
        )

    def test_remove_artist(self):
        john = mommy.make("User", username="john.doe")
        john.profile.email_activated = True
        john.profile.notify = True
        john.profile.save()

        # John follows one artist.
        nerf_herder = mommy.make(
            "app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867"
        )
        mommy.make("app.UserArtist", user=john, artist=nerf_herder)

        # John removes the only artist he's following.
        response = self.app.post(
            "/artists-remove", {"id": "da66103a-1307-400d-8261-89d856126867"}, user="john.doe"
        )

        # A redirect occurs, follow it.
        assert response.status == "302 Found"
        assert response.url == "/artists"
        response = response.follow()

        # John is no longer following any artist.
        self.assertEqual(
            "Removed 1 artist.", response.html.find("div", "message success").text.strip()
        )
        assert john.favorite_artists.count() == 0
