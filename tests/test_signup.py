from django.contrib.auth.models import User
from django_webtest import WebTest

from app.models import UserProfile


class TestSignUp(WebTest):
    """
    A user must be able to create an account.
    """

    def test_sign_up(self):
        # There is no user in the beginning.
        assert User.objects.count() == 0
        assert UserProfile.objects.count() == 0

        # The user opens the signup page.
        response = self.app.get("/signup")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == True

        # The user fills and submits the signup form.
        form = response.form
        form["email"] = "john@doe.local"
        form["password"] = "verysecret"
        response = form.submit()

        # After signup, a redirect is going to happen.
        assert response.status == "302 Found"
        assert response.url == "/signup-complete"

        # A user has been created.
        assert User.objects.count() == 1
        john_doe = User.objects.first()
        assert john_doe.is_active == True

        # A user profile has been created automatically.
        assert UserProfile.objects.count() == 1

        # But the email address is not confirmed yet.
        assert john_doe.profile.email_activated == False

        # Finally the user is being redirected and authenticated.
        response = response.follow()
        assert response.context["user"].is_anonymous == False
        assert response.context["user"] == john_doe
