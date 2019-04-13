# coding: utf-8
"""
Test timeutils
"""
import pytz
import datetime
from sugar.utils import timeutils


class TestTimeUtils:
    """
    time utils test.
    """
    def test_dump_iso_with_tz(self):
        """
        Test if time can be dumped to the ISO.

        :return:
        """
        dtm = pytz.utc.localize(datetime.datetime(year=2019, month=4, day=1,
                                                  hour=20, minute=15, second=30, microsecond=700000))
        assert timeutils.to_iso(dtm=dtm) == "2019-04-01T20:15:30.700000+00:00"

    def test_dump_iso_no_tz(self):
        """
        Test if time can be dumped to the ISO.

        :return:
        """
        dtm = datetime.datetime(year=2019, month=4, day=1, hour=20, minute=15, second=30, microsecond=700000)
        assert timeutils.to_iso(dtm=dtm) == "2019-04-01T20:15:30.700000+00:00"

    def test_parse_iso_with_tz(self):
        """
        Test parse ISO format with timezone.

        :return:
        """
        parsed_dtm = timeutils.from_iso("2019-04-01T20:15:30.700000+00:00")
        dtm = pytz.utc.localize(datetime.datetime(year=2019, month=4, day=1,
                                                  hour=20, minute=15, second=30, microsecond=700000))
        assert parsed_dtm == dtm

    def test_parse_iso_no_tz(self):
        """
        Test parse ISO format without timezone.

        :return:
        """
        parsed_dtm = timeutils.from_iso("2019-04-01T20:15:30.700000")
        dtm = pytz.utc.localize(datetime.datetime(year=2019, month=4, day=1,
                                                  hour=20, minute=15, second=30, microsecond=700000))
        assert parsed_dtm == dtm
