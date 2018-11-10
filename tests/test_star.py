from django_webtest import WebTest
from model_mommy import mommy

from app import models


class TestStar(WebTest):
    """
    Test the starring of releases
    """

    csrf_checks = False

    def test_star(self):
        release = mommy.make("app.ReleaseGroup", is_deleted=False)

        response = self.app.post("/star", {"id": release.id, "value": 1}, user="john_doe")
        assert response.status == "200 OK"
        assert response.content == "{}"

        assert models.Star.objects.count() == 1
        assert models.Star.objects.first().user.username == u"john_doe"
        assert models.Star.objects.first().release_group == release

    def test_unstar(self):
        release = mommy.make("app.ReleaseGroup", is_deleted=False)

        self.app.post("/star", {"id": release.id, "value": 1}, user="john_doe")
        assert models.Star.objects.count() == 1

        self.app.post("/star", {"id": release.id, "value": 0}, user="john_doe")
        assert models.Star.objects.count() == 0

    def test_star_anonymous_user(self):
        release = mommy.make("app.ReleaseGroup", is_deleted=False)

        response = self.app.post("/star", {"id": release.id, "value": 1})
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/star"

    def test_star_with_get_request(self):
        response = self.app.get("/star", user="john_doe")
        assert response.status == "302 Found"
        assert response.url == "/"

    def test_star_with_get_request_and_anonymous_user(self):
        response = self.app.get("/star")
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/star"
