from django_webtest import WebTest
from model_mommy import mommy


class TestFeed(WebTest):
    """
    Test the feed view.
    """

    def test_with_anonymous_user(self):
        response = self.app.get("/feed", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_non_existing_legacy_id(self):
        response = self.app.get("/feed?id=1", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_legacy_id(self):
        john = mommy.make("User", username="john.doe")
        john.profile.legacy_id = 42
        john.profile.save()

        response = self.app.get("/feed?id=42")
        assert response.status == "301 Moved Permanently"

    def test_with_non_existing_username(self):
        response = self.app.get("/feed?id=john.doe", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_username_without_stars(self):
        mommy.make("User", username="john.doe")

        response = self.app.get("/feed?id=john.doe")
        assert response.status == "200 OK"
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n    '
            '<title type="text">[muspy] New Releases</title>\n    '
            '<link href="http://testserver/feed?id=john.doe" rel="self" type="application/atom+xml" />\n    '
            '<link href="http://testserver/" rel="alternate" type="text/html" />\n    '
            "<id>http://testserver/feed?id=john.doe</id>\n    "
            "<updated>None</updated>\n    "
            "<author><name>muspy</name></author>\n    "
            "<icon>/static/favicon.ico</icon>\n    "
            "<logo>/static/logo.gif</logo>\n    \n"
            "</feed>\n",
            response.content,
        )

    def test_with_not_existing_username_without_stars(self):
        john = mommy.make("User", username="john.doe")
        nerf_herder = mommy.make("app.Artist", name="Nerf Herder")
        album = mommy.make(
            "app.ReleaseGroup",
            artist=nerf_herder,
            name="Rockingham",
            type="Album",
            is_deleted=False,
            date=20160221,
        )
        mommy.make("app.Star", user=john, release_group=album)
        mommy.make("app.UserArtist", user=john, artist=nerf_herder)

        response = self.app.get("/feed?id=john.doe")
        assert response.status == "200 OK"
        # TODO: Assert the content of the XML. Make sure the release is in the feed.
