from django.contrib.auth.models import User
from django_webtest import WebTest

from app import models


class TestDeleteForm(WebTest):
    """
    Test the delete form view which renders the form.
    """

    def test_delete_form_anonymous_user(self):
        response = self.app.get("/delete")
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/delete"

    def test_delete_form_authenticated_user(self):
        response = self.app.get("/delete", user="john.doe")
        assert response.status == "200 OK"


class TestDeleteFormSubmit(WebTest):
    """
    Test the submission of the delete form.
    """

    csrf_checks = False

    def test_delete_form_anonymous_user(self):
        response = self.app.post("/delete", expect_errors=True)
        assert response.status == "302 Found"
        assert response.url == "/signin?next=/delete"

    def test_delete_form_authenticated_user(self):
        response = self.app.get("/delete", user="john.doe")
        assert response.status == "200 OK"
        assert User.objects.count() == 1
        assert models.UserProfile.objects.count() == 1

        # Submit the confirmation form.
        response = response.form.submit().follow()
        assert response.status == "200 OK"

        assert User.objects.count() == 0
        assert models.UserProfile.objects.count() == 0
