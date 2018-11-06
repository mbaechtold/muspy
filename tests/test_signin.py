from django.contrib.auth.models import User
from django_webtest import WebTest


class TestSignIn(WebTest):

    def test_sign_in_with_non_existing_user(self):
        response = self.app.get("/signin")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == True

        form = response.form
        form["username"] = "user-does-not-exist@domain.local"
        form["password"] = "does-not-matter"
        response = form.submit()
        assert response.status == "200 OK"

        error_message = u"Please enter a correct username and password. Note that both fields may be case-sensitive."
        assert response.html.find("ul", "errorlist").find('li').text == error_message

        assert response.context["user"].is_anonymous == True

    def test_sign_in_wiht_wrong_password(self):
        john = User.objects.create(username="john.doe", email="john@doe.local")
        john.set_password('foo')
        john.save()

        response = self.app.get("/signin")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == True

        form = response.form
        form["username"] = "john@doe.local"
        form["password"] = "bar"
        response = form.submit()
        assert response.status == "200 OK"

        error_message = u"Please enter a correct username and password. Note that both fields may be case-sensitive."
        assert response.html.find("ul", "errorlist").find('li').text == error_message

        assert response.context["user"].is_anonymous == True

    def test_sign_in_with_correct_password(self):
        john = User.objects.create(username="john.doe", email="john@doe.local")
        john.set_password('foo')
        john.save()

        response = self.app.get("/signin")
        assert response.status == "200 OK"
        assert response.context["user"].is_anonymous == True

        form = response.form
        form["username"] = "john@doe.local"
        form["password"] = "foo"
        response = form.submit().follow()

        # If the authentication was successful, the user is redirected to the "/artists" view.
        assert response.status == "200 OK"
        assert response.request.url == 'http://testserver/artists'
        assert response.context["user"].is_anonymous == False
