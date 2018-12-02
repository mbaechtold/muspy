from unittest.mock import patch

from django.contrib.auth.models import User
from django_webtest import WebTest


@patch("app.views.tasks.get_release_groups_by_artist.delay")
@patch("app.views.tasks.update_cover_art_by_mbid.delay")
class TestIndex(WebTest):
    """
    Test the index view.
    """

    def test_index_redirects_authenticated_user_to_artists_view(self, *args, **kwargs):
        john_doe = User.objects.create(username="john.doe", email="john@doe.local")
        john_doe.set_password("very_secret")

        response = self.app.get("/", user="john.doe")
        assert response.status == "302 Found"
        assert response.url == "/artists"
