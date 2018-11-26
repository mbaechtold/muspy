from django_webtest import TransactionWebTest
from freezegun import freeze_time
from model_mommy import mommy


class TestIcal(TransactionWebTest):
    """
    Test the ical view.
    """

    reset_sequences = True

    def test_redirect(self):
        response = self.app.get("/ical?id=john.doe")
        assert response.status == "302 Found"
        assert response.url == "/ical/john.doe"

    def test_with_non_existing_legacy_id(self):
        response = self.app.get("/ical/1", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_legacy_id(self):
        john = mommy.make("User", username="john.doe")
        john.profile.legacy_id = 42
        john.profile.save()

        response = self.app.get("/ical/42", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_non_existing_username(self):
        response = self.app.get("/ical/john.doe", expect_errors=True)
        assert response.status == "404 Not Found"

    def test_with_existing_username_without_stars(self):
        mommy.make("User", username="john.doe")

        response = self.app.get("/ical/john.doe")
        assert response.status == "200 OK"
        self.assertEqual(
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//testserver//1.0//EN\r\n"
            b"CALSCALE:GREGORIAN\r\n"
            b"METHOD:PUBLISH\r\n"
            b"X-WR-CALNAME:Muspy\r\n"
            b"X-WR-TIMEZONE:UTC\r\n"
            b"END:VCALENDAR\r\n",
            response.content,
        )

    def test_with_existing_username_with_stars(self):
        john = mommy.make("User", username="john.doe")
        nerf_herder = mommy.make(
            "app.Artist", name="Nerf Herder", mbid="da66103a-1307-400d-8261-89d856126867"
        )
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

        freezer = freeze_time("2017-01-01 15:00")
        freezer.start()

        response = self.app.get("/ical/john.doe")
        assert response.status == "200 OK"
        self.assertEqual(
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//testserver//1.0//EN\r\n"
            b"CALSCALE:GREGORIAN\r\n"
            b"METHOD:PUBLISH\r\n"
            b"X-WR-CALNAME:Muspy\r\n"
            b"X-WR-TIMEZONE:UTC\r\n"
            b"BEGIN:VEVENT\r\n"
            b"SUMMARY:Nerf Herder - Rockingham\r\n"
            b"DTSTART;VALUE=DATE:20160221\r\n"
            b"DTEND;VALUE=DATE:20160222\r\n"
            b"DTSTAMP;VALUE=DATE-TIME:20170101T150000Z\r\n"
            b"UID:1@testserver\r\n"
            b"CATEGORIES:\r\n"
            b"DESCRIPTION:\r\n"
            b"URL:http://example.com/artist/da66103a-1307-400d-8261-89d856126867\r\n"
            b"END:VEVENT\r\n"
            b"END:VCALENDAR\r\n",
            response.content,
        )

        freezer.stop()
