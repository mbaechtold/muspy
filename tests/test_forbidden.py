from django_webtest import WebTest


class TestForbidden(WebTest):
    """
    Test the "forbidden" view.
    """

    def test_forbidden_view(self):
        response = self.app.get("/blog|foo.php", expect_errors=True)
        assert response.status == "403 Forbidden"
