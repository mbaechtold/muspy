from django_webtest import WebTest
from model_mommy import mommy

from app import models


class TestResetForm(WebTest):
    """
    Test the password reset form view.
    """

    csrf_checks = False

    def test_reset_form_nonexisting_user(self):
        response = self.app.get("/reset")
        form = response.form
        form["email"] = "does@not.exist"
        response = form.submit()
        assert response.status == "200 OK"
        self.assertEqual(
            u"Unknown email address. Please enter another.",
            response.html.find("ul", "errorlist").text,
        )

    def test_reset_form_existing_user(self):
        john = mommy.make("User", email="john@doe.local")

        response = self.app.get("/reset")
        form = response.form
        form["email"] = "john@doe.local"
        response = form.submit().follow()
        assert response.status == "200 OK"
        self.assertEqual(
            u"An email has been sent to john@doe.local describing how to obtain your new password.",
            response.html.find("div", "message success").text.strip(),
        )

        # A reset code has been created on the user profile.
        john.profile.refresh_from_db()
        assert len(john.profile.reset_code) > 0

    def test_reset_form_existing_user_without_profile(self):
        john = mommy.make("User", email="john@doe.local")

        # A profile has been created automatically, delete it.
        john.profile.delete()
        assert models.UserProfile.objects.count() == 0

        response = self.app.get("/reset")
        form = response.form
        form["email"] = "john@doe.local"
        response = form.submit()
        assert response.status == "200 OK"
        self.assertEqual(
            u"Unknown email address. Please enter another.",
            response.html.find("ul", "errorlist").text,
        )


class TestResetCode(WebTest):
    """
    Test the user resetting his password.
    """

    def test_reset_code_not_found(self):
        response = self.app.get("/reset?code=doesnotexist")
        assert response.status == "200 OK"
        self.assertEqual(
            u"Invalid code, your password was not reset.",
            response.html.find("div", id="content").find("p").text,
        )

    def test_reset_code_available(self):
        john_doe = mommy.make("User", email="john@doe.local")

        # Generate a reset code.
        john_doe.profile.send_reset_email()

        # The user clicks the link in the email.
        response = self.app.get("/reset?code={}".format(john_doe.profile.reset_code))

        # The user has been redirect to the settings page, where he should set a new password.
        assert response.status == "302 Found"
        assert response.url == "/settings"
        response = response.follow()
        assert response.status == "200 OK"

        # The user is logged in automatically.
        assert response.context["user"].is_anonymous == False
        assert response.context["user"] == john_doe
