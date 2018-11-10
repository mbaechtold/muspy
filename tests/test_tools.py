from django_webtest import WebTest

from app.tools import arrange_for_table
from app.tools import date_to_iso8601
from app.tools import date_to_str
from app.tools import str_to_date


class TestTools(WebTest):
    def test_arrange_for_table(self):
        assert arrange_for_table(["a", "b", "c", "d"], 3) == [["a", "c", "d"], ["b", None, None]]

    def test_str_to_date(self):
        assert str_to_date(False) == 0
        assert str_to_date("AAAA-01-02") == 0
        assert str_to_date("2010-01-02") == 20100102
        assert str_to_date("2010-01") == 20100100
        assert str_to_date("2010") == 20100000

    def test_date_to_str(self):
        assert date_to_str(0) == "0"
        assert date_to_str(20100102) == "2010-01-02"
        assert date_to_str(20100100) == "2010-01"
        assert date_to_str(20100000) == "2010"

    def test_date_to_iso8601(self):
        assert date_to_iso8601(20100203) == "2010-02-03T00:00:00Z"
        assert date_to_iso8601(20100200) == "2010-02-01T00:00:00Z"
        assert date_to_iso8601(20100000) == "2010-01-01T00:00:00Z"
