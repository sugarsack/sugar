# coding: utf-8
"""
Query parser test
"""
from sugar.components.server.query import QueryBlock


class TestServerQueryBlock:
    """
    Test suite for query block matcher, parser etc.
    """

    def test_simple_query_all(self):
        """
        Test simple query:

          <target>
          :[flags]:<target>

        :return:
        """
        qbl = QueryBlock("*")

        assert qbl.target == r'.*\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

    def test_simple_query_fullname(self):
        """
        Test simple query for fullname.

          <target>
          :[flags]:<target>

        :return:
        """
        qbl = QueryBlock("somehost")

        assert qbl.target == r'somehost\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

    def test_short_query(self):
        """
        Test short query parsing:

          [flags]:<target>
          [trait]:<target>
          [trait]:[flags]:<target>

        :return:
        """
