from django_webtest import WebTest
from freezegun import freeze_time
from model_mommy import mommy


class TestIcal(WebTest):
    """
    Test the ical view.
    """

    def test_with_anonymous_user(self):
        response = self.app.get("/ical", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_non_existing_legacy_id(self):
        response = self.app.get("/ical?id=1", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_legacy_id(self):
        john = mommy.make("User", username="john.doe")
        john.profile.legacy_id = 42
        john.profile.save()

        response = self.app.get("/ical?id=42", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_non_existing_username(self):
        response = self.app.get("/ical?id=john.doe", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_username_without_stars(self):
        mommy.make("User", username="john.doe")

        response = self.app.get("/ical?id=john.doe")
        assert response.status == "200 OK"
        self.assertEqual(
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Muspy//Muspy releases//EN\r\n"
            "END:VCALENDAR\r\n",
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

        response = self.app.get("/ical?id=john.doe")
        assert response.status == "200 OK"
        self.assertEqual(
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Muspy//Muspy releases//EN\r\n"
            "BEGIN:VEVENT\r\n"
            "SUMMARY:Nerf Herder - Rockingham\r\n"
            "DTSTART;VALUE=DATE:20160221\r\n"
            "DTEND;VALUE=DATE:20160222\r\n"
            "UID:1-john.doe@muspy.com\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n",
            response.content,
        )
