from django_webtest import WebTest


class TestSignOut(WebTest):
    """
    A user must be able to sign out.
    """

    def test_sign_out(self):
        response = self.app.get("/", user="john.doe", auto_follow=True)
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == False
        assert response.context["user"].username == "john.doe"

        response = response.click("Sign out")
        response = response.follow()
        assert response.context["user"].is_anonymous == True
