from django.contrib.auth.models import User
from django_webtest import WebTest


class TestActivation(WebTest):
    """
    A user must be able to activate her account.
    """
    def test_resend_activation(self):
        # Create a user we can work with in this test.
        john_doe = User.objects.create(username="john.doe", email="john@doe.local")
        john_doe.set_password("very_secret")

        # The user signs in.
        response = self.app.get("/", user="john.doe")
        assert response.context["user"].is_anonymous == False
        assert response.context["user"] == john_doe

        # The user requests an activation code.
        self.app.get("/activate")
        john_doe.profile.refresh_from_db()
        activation_code = john_doe.profile.activation_code

        # The user requests another activation code.
        self.app.get("/activate")
        john_doe.profile.refresh_from_db()

        # The user's activation code has changed.
        assert john_doe.profile.activation_code != activation_code
