from django.contrib.auth.models import User
from django_webtest import WebTest


class TestActivation(WebTest):
    """
    A user must be able to activate her account.
    """

    def test_anonymous_user(self):
        """
        Anonymous users cannot request an email activation. Users must sign in first
        otherwise we cannot get the email address to send the activation email to.
        """
        response = self.app.get("/activate")
        assert response.status == "302 Found"
        assert response.url == "/"

    def test_activation_after_signup(self):
        # The user opens the signup page.
        response = self.app.get("/signup")

        # The user fills and submits the signup form.
        form = response.form
        form["email"] = "john@doe.local"
        form["password"] = "verysecret"
        response = form.submit().follow()

        # The user is authenticated (see signup view).
        john_doe = response.context["user"]

        # The email address is not yet activated.
        assert john_doe.profile.email_activated == False

        # The user clicks the activation link in the mail.
        self.app.get(f"/activate?code={john_doe.profile.activation_code}")

        # Now the email address is yet activated.
        john_doe.profile.refresh_from_db()
        assert john_doe.profile.email_activated == True

    def test_resend_activation(self):
        # Create a user we can work with in this test.
        john_doe = User.objects.create(username="john.doe", email="john@doe.local")
        john_doe.set_password("very_secret")

        # The user signs in.
        response = self.app.get("/", user="john.doe")
        assert response.context["user"].is_anonymous == False
        assert response.context["user"] == john_doe

        # The user requests an activation code.
        response = self.app.get("/activate")
        form = response.form
        response = form.submit().follow()
        assert response.status == "200 OK"

        # The email address is not yet activated.
        john_doe.profile.refresh_from_db()
        assert john_doe.profile.email_activated == False

        # The user clicks the activation link in the mail.
        self.app.get(f"/activate?code={john_doe.profile.activation_code}")

        # Now the email address is yet activated.
        john_doe.profile.refresh_from_db()
        assert john_doe.profile.email_activated == True

    def test_authenticated_user_with_activate_email(self):
        # Create a user we can work with in this test.
        john_doe = User.objects.create(username="john.doe", email="john@doe.local")
        john_doe.profile.email_activated = True
        john_doe.profile.save()

        # The user signs in and manually opens the activation view.
        response = self.app.get("/activate", user="john.doe")

        # The user won't see the activation view, because its email is already activated.
        assert response.status == "302 Found"
        assert response.url == "/"

        # The user sees a message instead.
        response = response.follow()
        assert response.status == "200 OK"
        error_message = "Your email address is already active."
        assert response.html.find("div", "message").find("p").text == error_message
