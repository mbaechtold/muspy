from unittest.mock import patch

from django.contrib.auth.models import User
from django_webtest import WebTest
from model_mommy import mommy


@patch("app.views.tasks.get_release_groups_by_artist.delay")
class TestArtistsAdd(WebTest):
    """
    Test the "artists add" view.

    # TODO: We need to mock the LastFM API calls so we don't hit LastFM during the tests.
    """

    csrf_checks = False

    def test_with_anonymous_user(self, *args, **kwargs):
        response = self.app.get("/artists-add", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/artists-add"

    def test_add_blacklisted_artist(self, *args, **kwargs):
        john = mommy.make("User", username="john.doe")
        john.profile.email_activated = True
        john.profile.notify = True
        john.profile.save()
        response = self.app.get("/artists-add?id=89ad4ac3-39f7-470e-963a-56509c546377", user=john)

        # A redirect occurred.
        assert response.status == "302 Found"
        assert response.url == "/artists"

        # Follow th redirect.
        response = response.follow()
        assert response.status == "200 OK"

        self.assertEqual(
            "The artist is special-purpose and cannot be added",
            response.html.find("div", "message error").text.strip(),
        )
        assert User.objects.get(username="john.doe").favorite_artists.count() == 0

    def test_add_artist(self, *args, **kwargs):
        john = mommy.make("User", username="john.doe")
        john.profile.email_activated = True
        john.profile.notify = True
        john.profile.save()
        response = self.app.get("/artists-add?id=da66103a-1307-400d-8261-89d856126867", user=john)

        # A redirect occurred.
        assert response.status == "302 Found"
        assert response.url == "/artists"

        # Follow th redirect.
        response = response.follow()
        assert response.status == "200 OK"

        self.assertEqual(
            "Nerf Herder has been added!", response.html.find("div", "message success").text.strip()
        )
        assert User.objects.get(username="john.doe").favorite_artists.count() == 1
