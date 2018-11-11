from django_webtest import TransactionWebTest
from model_mommy import mommy


class TestIcal(TransactionWebTest):
    """
    Test the ical view.
    """

    reset_sequences = True

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
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//Muspy//Muspy releases//EN\r\n"
            b"END:VCALENDAR\r\n",
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
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//Muspy//Muspy releases//EN\r\n"
            b"BEGIN:VEVENT\r\n"
            b"SUMMARY:Nerf Herder - Rockingham\r\n"
            b"DTSTART;VALUE=DATE:20160221\r\n"
            b"DTEND;VALUE=DATE:20160222\r\n"
            b"UID:1-john.doe@muspy.com\r\n"
            b"END:VEVENT\r\n"
            b"END:VCALENDAR\r\n",
            response.content,
        )
