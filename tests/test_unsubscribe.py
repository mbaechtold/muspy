from django_webtest import WebTest
from model_mommy import mommy

from app import models


class TestUnsubscribe(WebTest):
    """
    Test the unsubscribe view.
    """

    def test_unsubscribe_without_params(self):
        response = self.app.get("/unsubscribe")
        assert response.status == "302 Found"
        assert response.url == "/"

        # A redirect occurred, let's follow it.
        response = response.follow()
        assert response.status == "200 OK"

        self.assertEqual(
            u"Bad request, you were not unsubscribed.",
            response.html.find("div", "message error").text.strip(),
        )

    def test_reset_form_with_existing_user_not_having_a_profile(self):
        john = mommy.make("User", username="john.doe")

        # A profile has been created automatically, delete it.
        john.profile.delete()
        assert models.UserProfile.objects.count() == 0

        # The user tries to unsubscribe.
        response = self.app.get("/unsubscribe?id={}".format(john.username))
        assert response.status == "302 Found"
        assert response.url == "/"

        # A redirect occurred, let's follow it.
        response = response.follow()
        assert response.status == "200 OK"

        self.assertEqual(
            u"Bad request, you were not unsubscribed.",
            response.html.find("div", "message error").text.strip(),
        )

    def test_reset_form_with_existing_user(self):
        john = mommy.make("User", email="john@doe.local")
        assert john.profile.notify == True

        # The user tries to unsubscribe.
        response = self.app.get("/unsubscribe?id={}".format(john.username))
        assert response.status == "302 Found"
        assert response.url == "/"

        # A redirect occurred, let's follow it.
        response = response.follow()
        assert response.status == "200 OK"

        self.assertEqual(
            u"You have successfully unsubscribed from release notifications. If you change your mind, you can subscribe to notifications on the Settings page.",
            response.html.find("div", "message success").text.strip(),
        )
        john.profile.refresh_from_db()
        assert john.profile.notify == False
