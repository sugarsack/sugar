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

    def test_simplequery_fullname_asterisk(self):
        """
        Test simple query for fullname with asterisks.

        :return:
        """
        qbl = QueryBlock("somehost*")
        assert qbl.target == r'somehost.*\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

        qbl = QueryBlock("*somehost")
        assert qbl.target == r'.*somehost\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

        qbl = QueryBlock("some*host")
        assert qbl.target == r'some.*host\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

    def test_simplequery_fullname_subnames(self):
        """
        Test simple query for full name with sub-names.

        :return:
        """
        qbl = QueryBlock("web[1-3]")
        assert qbl.target == r'web[1-3]\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

        qbl = QueryBlock("web[1,3]")
        assert qbl.target == r'web[1,3]\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

    def test_partialquery_all(self):
        """
        Test partial query for 'a' flag.

        :return:
        """
        for query in [':a:', 'a:']:
            qbl = QueryBlock(query)
            assert qbl.target == r'.*\Z(?ms)'
            assert qbl.trait is None
            assert qbl.flags == ()

    def test_partialquery_fullname(self):
        """
        Test partial query for full name.

        :return:
        """
        qbl = QueryBlock(":-r:somehost")
        assert qbl.target == r'somehost'
        assert qbl.trait is None
        assert qbl.flags == ('r',)

        qbl = QueryBlock(":-c:somehost")
        assert qbl.target == r'somehost\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('c',)

        qbl = QueryBlock(":-rcx:somehost")
        assert qbl.target == r"somehost"
        assert qbl.trait is None
        assert sorted(qbl.flags) == sorted(("r", "c", "x"))

    def test_partialquery_fullname_glob_case_sensitive(self):
        """
        Test partial query for full name with the globbing.

        :return:
        """
        qbl = QueryBlock(":-x:SOMEHOST*")
        assert qbl.target == r'somehost.*\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('x',)

        qbl = QueryBlock(":-c:*SOMEHOST")
        assert qbl.target == r'.*SOMEHOST\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('c',)

        qbl = QueryBlock(":-c:Some*Host")
        assert qbl.target == r'Some.*Host\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('c',)

    def test_traits_query_basic(self):
        """
        Test short query parsing:

          [flags]:<target>
          [trait]:<target>
          [trait]:[flags]:<target>

        :return:
        """
        qbl = QueryBlock("os-family:-c:Debian")
        assert qbl.target == r'Debian\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('c',)

        qbl = QueryBlock("os-family:-x:DEBIAN")
        assert qbl.target == r'debian\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

        qbl = QueryBlock("os-family:-x:DEBIAN*")
        assert qbl.target == r'debian.*\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

        qbl = QueryBlock("os-family:-x:*DEBIAN*")
        assert qbl.target == r'.*debian.*\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

    def test_traits_query_regex(self):
        """
        Test traits query regular expression.

        :return:
        """
        qbl = QueryBlock("os-family:-r:(Debian|Ubuntu|SUSE|RedHat)")
        assert qbl.target == r'(debian|ubuntu|suse|redhat)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('r',)

