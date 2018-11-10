from django.contrib.auth.models import User
from django_webtest import WebTest

from app.models import UserProfile


class TestDeleteAccount(WebTest):
    """
    A user must be able to delete her account.
    """

    def test_delete_account(self):
        john_doe = User.objects.create(username="john.doe", email="john@doe.local")
        assert User.objects.count() == 1

        # A user profile has been created automatically.
        assert UserProfile.objects.count() == 1
        john_doe_profile = UserProfile.objects.first()
        assert john_doe_profile.user == john_doe

        response = self.app.get("/settings", user=john_doe)
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == False
        assert response.context["user"].username == u"john.doe"

        # There a two forms on the settings page. Submit the second form.
        response = response.forms[1].submit()
        assert response.status == "200 OK"
        assert response.request.url == "http://testserver/delete"

        # Submit the confirmation form.
        response = response.form.submit().follow()
        assert response.status == "200 OK"
        assert response.request.url == "http://testserver/"

        # The user has been deleted.
        assert User.objects.count() == 0
        assert response.context["user"].is_anonymous == True

        # The profile has been deleted too.
        assert UserProfile.objects.count() == 0
