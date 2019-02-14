# coding: utf-8
"""
Query parser test.
"""
import pytest
from sugar.components.server.query import QueryBlock, Query


@pytest.fixture
def hosts_list() -> list:
    """
    Get a list of hosts.

    :return: list
    """
    hosts = [
        "web1.example.org", "web2.example.org", "web3.example.org", "web4.example.org", "web5.example.org",
        "web1.sugarsack.org", "web2.sugarsack.org", "web3.sugarsack.org", "web4.sugarsack.org", "web5.sugarsack.org",
        "zoo1.domain.com", "zoo2.domain.com", "zoo3.domain.com", "zoo4.domain.com", "zoo5.domain.com",
        "zoo1", "zoo2", "zoo3", "zoo4", "zoo5",
    ]

    return hosts


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
        qbl = QueryBlock(":r:somehost")
        assert qbl.target == r'somehost'
        assert qbl.trait is None
        assert qbl.flags == ('r',)

        qbl = QueryBlock(":c:somehost")
        assert qbl.target == r'somehost\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('c',)

        qbl = QueryBlock(":rcx:somehost")
        assert qbl.target == r"somehost"
        assert qbl.trait is None
        assert sorted(qbl.flags) == sorted(("r", "c", "x"))

    def test_partialquery_fullname_glob_case_sensitive(self):
        """
        Test partial query for full name with the globbing.

        :return:
        """
        qbl = QueryBlock(":x:SOMEHOST*")
        assert qbl.target == r'somehost.*\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('x',)

        qbl = QueryBlock(":c:*SOMEHOST")
        assert qbl.target == r'.*SOMEHOST\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ('c',)

        qbl = QueryBlock(":c:Some*Host")
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
        qbl = QueryBlock("os-family:c:Debian")
        assert qbl.target == r'Debian\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('c',)

        qbl = QueryBlock("os-family:x:DEBIAN")
        assert qbl.target == r'debian\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

        qbl = QueryBlock("os-family:x:DEBIAN*")
        assert qbl.target == r'debian.*\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

        qbl = QueryBlock("os-family:x:*DEBIAN*")
        assert qbl.target == r'.*debian.*\Z(?ms)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('x',)

    def test_traits_query_regex(self):
        """
        Test traits query regular expression.

        :return:
        """
        qbl = QueryBlock("os-family:r:(Debian|Ubuntu|SUSE|RedHat)")
        assert qbl.target == r'(debian|ubuntu|suse|redhat)'
        assert qbl.trait == "os-family"
        assert qbl.flags == ('r',)

    def test_traits_all_flag(self):
        """
        Test if 'a' flag invalidates everything (it should)
        :return:
        """
        qbl = QueryBlock("os-family:ar:(Debian|Ubuntu|SUSE|RedHat)")
        assert qbl.target == r'.*\Z(?ms)'
        assert qbl.trait is None
        assert qbl.flags == ()

    def test_simple_list(self):
        """
        Test simple query listing.

        :return:
        """
        qbl = QueryBlock("foo,bar,fred")
        assert qbl.target == r"(foo\Z(?ms)|bar\Z(?ms)|fred\Z(?ms))"
        assert qbl.trait is None
        assert qbl.flags == ("r",)

    def test_simple_globbing_list(self):
        """
        Test simple globbing query listing.

        :return:
        """
        qbl = QueryBlock("foo*,*bar,fr*ed")
        assert qbl.target == r"(foo.*\Z(?ms)|.*bar\Z(?ms)|fr.*ed\Z(?ms))"
        assert qbl.trait is None
        assert qbl.flags == ("r",)


class TestServerQueryMatcher:
    """
    Test suite for server query matcher.
    """
    def test_select_all_query(self, hosts_list):
        """
        Test 'get all' query, both by globbing and flag-based.

        :param hosts_list: list of hosts
        :return:
        """
        for query in ["*", ":a", "a:", ":a:"]:
            qry = Query(query)
            assert len(qry.filter(hosts_list)) == len(hosts_list)
            assert set(qry.filter(hosts_list)) == set(hosts_list)

        assert Query("a").filter(hosts_list) == []

    def test_select_list_hosts(self, hosts_list):
        """
        Test list of hosts by full names, such as: "web1,web2,web3"

        :param hosts_list: list of hosts
        :return:
        """
        qry = Query("zoo1,web2*,web3.sugarsack.org")
        assert set(qry.filter(hosts_list)) == {"web3.sugarsack.org", "web2.sugarsack.org", "web2.example.org", "zoo1"}

    def test_select_subselect(self, hosts_list):
        """
        Select from previous select.

        :param hosts_list:
        :return:
        """
        for op in ["/", "&&", " and "]:
            assert Query("zoo[1,3,4]{op}zoo[2,4]".format(op=op)).filter(hosts_list) == ["zoo4"]

    def test_select_subsequent_after_trait(self, hosts_list):
        """

        :param hosts_list:
        :return:
        """
        for op in ["/", "&&", " and "]:
            qry = Query("os-name:debian{op}web[1,3]*".format(op=op))
            assert set(qry.filter(hosts_list)) == {'web1.example.org', 'web3.example.org',
                                                   'web1.sugarsack.org', 'web3.sugarsack.org'}

    def test_select_inversion_flag(self, hosts_list):
        """
        Test inverse query.

        :return:
        """
        qry = Query(":x:web*")
        assert set(qry.filter(hosts_list)) == {'zoo1.domain.com', 'zoo2.domain.com', 'zoo3.domain.com',
                                               'zoo4.domain.com', 'zoo5.domain.com',
                                               'zoo1', 'zoo2', 'zoo3', 'zoo4', 'zoo5'}

    def test_no_flags(self, hosts_list):
        """
        Test empty flags should not raise an exception (if there are just :: syntax).

        :return:
        """
        assert set(Query("hostname::web*").filter(hosts_list)) == set(hosts_list)

        hosts = Query("::web*").filter(hosts_list)
        assert set(hosts) == set([host for host in hosts_list if host.startswith("web")])

    def test_select_inversion_composite(self, hosts_list):
        """
        Test inversion composite query.

        :param hosts_list: list of the hosts fixture
        :return:
        """
        for op in ["/", "&&", " and "]:
            assert set(Query("zoo1,zoo2,zoo3{op}:x:zoo2".format(op=op)).filter(hosts_list)) == {"zoo1", "zoo3"}

    def test_union(self, hosts_list):
        """
        Test union query.

        :return:
        """
        for aop, oop in [("/", "//"), ("&&", "||"), (" and ", " or ")]:
            qry = Query("*.example.org,*.sugarsack.org,*.domain.com{a}:x:*[1-3]*{o}zoo[1-3]{a}:x:zoo[3]".format(
                a=aop, o=oop))
            assert set(qry.filter(hosts_list)) == {'web4.example.org', 'web4.sugarsack.org', 'web5.example.org',
                                                   'web5.sugarsack.org', 'zoo1', 'zoo2', 'zoo4.domain.com',
                                                   'zoo5.domain.com'}
