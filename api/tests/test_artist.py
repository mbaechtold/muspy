from unittest.mock import patch

from django.urls import reverse
from model_mommy import mommy
from rest_framework.test import APITestCase


class TestArtistApi(APITestCase):
    def test_non_existing_artist(self):
        response = self.client.get(
            reverse("api:artist-detail", args=["da66103a-1307-400d-8261-89d856126867"]),
            format="json",
        )
        assert response.status_code == 404

    @patch("app.views.tasks.get_release_groups_by_artist.delay")
    @patch("app.views.tasks.update_cover_art_by_mbid.delay")
    def test_existing_artist(self, *args, **kwargs):
        nerf_herder = mommy.make(
            "app.Artist",
            name="Nerf Herder",
            sort_name="Nerf Herder",
            mbid="da66103a-1307-400d-8261-89d856126867",
        )
        response = self.client.get(
            reverse("api:artist-detail", args=[nerf_herder.mbid]), format="json"
        )
        assert response.status_code == 200
        assert response.json() == {
            "mbid": "da66103a-1307-400d-8261-89d856126867",
            "name": "Nerf Herder",
            "disambiguation": "",
            "sort_name": "Nerf Herder",
        }
