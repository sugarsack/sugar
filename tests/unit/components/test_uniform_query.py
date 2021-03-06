# coding: utf-8
"""
Test uniform query.
"""

from sugar.components.server.query import Query
from sugar.components.server.pdatamatch import PDataContainer


class TestUniformQuery:
    """
    Test uniform data querying with multiple expressions.
    """
    uniform_data = []

    @classmethod
    def setup_class(cls):
        """
        Setup test suite runtime.

        :return:
        """
        hosts = [
            (
                "9d588bdf202b18b361fbcd75ef1659b7", "linux.host.com",
                {
                    "os-family": "Linux",
                    "machine-id": "9d588bdf202b18b361fbcd75ef1659b7",
                },
                {
                    "cluster": {
                        "type": "ceph",
                        "node": "5930ba4ff",
                    }
                },
            ),
            (
                "5895f46c218d0e93ad89b2b1c5ece70a", "slowlaris.host.com",
                {
                    "os-family": "SunOS",
                    "machine-id": "5895f46c218d0e93ad89b2b1c5ece70a",
                },
                {
                    "alias.name": "snorcle",
                },
            ),
            (
                "c5639506d94da96de7b77aa6e9539ad6", "bsd.host.com",
                {
                    "os-family": "FreeBSD",
                    "machine-id": "c5639506d94da96de7b77aa6e9539ad6",
                },
                {
                    "services": [
                        "nginx", "postfix", "postgresql",
                    ]
                },
            ),
        ]

        cls.uniform_data = []
        for mid, hname, traits, pdata in hosts:
            container = PDataContainer(mid, hname)
            container.traits = traits
            container.pdata = pdata
            cls.uniform_data.append(container)

    @classmethod
    def teardown_class(cls):
        """
        Teardown test suite runtime.

        :return:
        """
        cls.uniform_data = []

    def test_basic_traits(self):
        """
        Perform a basic uniform search over the data.

        :return:
        """
        out = Query("os-family:sunos").filter(self.uniform_data)
        assert len(out) == 1
        assert out[0].host == "slowlaris.host.com"

    def test_regex_traits(self):
        """
        Perform compound uniform search over the data.

        :return:
        """
        found = 0
        for meta in Query("os-family:r:(sunos|linux)").filter(self.uniform_data):
            found += 1
            assert meta.host != "bsd.host.com"
            assert meta.host in ["linux.host.com", "slowlaris.host.com"]

        assert found == 2

    def test_basic_cdata(self):
        """
        Basic search over cdata.

        :return:
        """
        out = Query("cluster.type:ceph").filter(self.uniform_data)
        assert len(out) == 1
        assert out[0].host == "linux.host.com"

    def test_basic_traits_compound(self):
        """
        Basic compound search for traits data.

        :return:
        """
        found = 0
        for meta in Query("os-family:r:(sunos|bsd) && os-family:bsd || os-family:linux").filter(self.uniform_data):
            found += 1
            assert meta.host != "slowlaris.host.com"
            assert meta.host in ["linux.host.com", "bsd.host.com"]

        assert found == 2

    def test_basic_cdata_compound(self):
        """
        Basic compound search for cdata.

        :return:
        """
        found = 0
        for meta in Query("cluster.type:ceph || services:nginx").filter(self.uniform_data):
            found += 1
            assert meta.host != "slowlaris.host.com"
            assert meta.host in ["linux.host.com", "bsd.host.com"]

        assert found == 2

    def test_basic_dotted_cdata(self):
        """
        Select basic transformable cdata.

        :return:
        """
        out = Query("alias-name:snorcle").filter(self.uniform_data)
        assert len(out) == 1
        assert out[0].host == "slowlaris.host.com"
