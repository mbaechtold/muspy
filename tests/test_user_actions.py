from django_webtest import WebTest


class TestUserAction(WebTest):
    """
    Test the visibility of the user actions in the menu e.g. sign in, sign up, settings, sign out, etc.
    """

    def test_user_actions_anonymous(self):
        """
        An anonymous user must see the user action for sign up and sign in.
        """
        response = self.app.get("/")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == True

        sign_in_link = response.html.find(lambda tag: tag.name == "a" and "Sign in" in tag.text)
        assert sign_in_link["href"] == "/signin"

        sign_up_link = response.html.find(lambda tag: tag.name == "a" and "Sign up" in tag.text)
        assert sign_up_link["href"] == "/signup"

    def test_user_actions_authenticated(self):
        """
        An authenticated user must be able to sign out and access the settings form.
        """
        response = self.app.get("/", user="john.doe")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == False
        assert response.context["user"].username == "john.doe"

        settings_link = response.html.find(lambda tag: tag.name == "a" and "Settings" in tag.text)
        assert settings_link["href"] == "/settings"

        sign_out_link = response.html.find(lambda tag: tag.name == "a" and "Sign out" in tag.text)
        assert sign_out_link["href"] == "/signout"
