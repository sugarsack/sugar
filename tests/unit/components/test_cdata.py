# config: utf-8
"""
Test client data matchers
"""
import pytest

from sugar.lib.compat import yaml
from sugar.components.server.cdatamatch import UniformMatch
from sugar.components.server.pdatastore import CDataContainer
from sugar.components.server.query import QueryBlock, Query


@pytest.fixture
def matcher():
    """
    Inherency data example.

    :return:
    """
    data = """
- one
- two
- key:
    - value
    - othervalue
    - innerkey:
        - innervalue
        - otherinnerkey: somevalue
- some.key: value
- complex.path:
    - with.nested:
      - keys.here.there: value
- mixed-name.key: value
    """

    cnt = CDataContainer("han-solo", "hansolo.org")
    cnt.traits = {
        "os-family": "Linux",
        "os-major-version": "10",
        "ipv4": [
            "10.160.5.104",
            "127.0.0.1",
            "192.168.0.2",
        ],
        "hwaddr-interfaces": {
            "eth0": "68:f7:28:d0:d0:5b",
            "virbr0": "52:54:00:77:fe:05",
            },
        "cluster": {
            "ceph": {
                "node": "5aceb7fc",
            }
        },
        "ip.v4": "10.10.10.10",
        "items": [1, 2, 3, 4],
    }
    cnt.pdata = yaml.load(data)

    return UniformMatch(cnt)


class TestUniformMatcher:
    """
    Test suite to test uniform matcher.
    """

    def test_basic_value(self, matcher):
        """
        Test basic matcher against one value.

        :return:
        """
        assert matcher.match(QueryBlock(":d:one"))
        assert matcher.match(QueryBlock(":d:o*"))
        assert not matcher.match(QueryBlock(":d:three"))

    def test_basic_value_list(self, matcher):
        """
        Test basic list matcher against several values in the list.

        :return:
        """
        assert matcher.match(QueryBlock(":d:one,two,three"))
        assert matcher.match(QueryBlock(":d:one,three"))
        assert matcher.match(QueryBlock(":d:four,three,two"))
        assert matcher.match(QueryBlock(":d:four,three,o*"))
        assert matcher.match(QueryBlock(":d:four,three,*e"))
        assert matcher.match(QueryBlock(":d:a*,*e"))
        assert not matcher.match(QueryBlock(":d:four,three"))

    def test_basic_traits_by_key(self, matcher):
        """
        Match cdata by keys.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("os-family:Linux"))
        assert matcher.match(QueryBlock("os-family:linux"))
        assert matcher.match(QueryBlock("os-family:lin*"))
        assert matcher.match(QueryBlock("os-family:*ux"))
        assert matcher.match(QueryBlock("os-major-version:10"))
        assert not matcher.match(QueryBlock("os-major-version:11"))
        assert not matcher.match(QueryBlock("os-family:c:linux"))
        assert matcher.match(QueryBlock("os-family:c:Linux"))

    def test_basic_traits_by_multikey(self, matcher):
        """
        Match cdata traits by nested keys.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("cluster.ceph.node:5aceb7fc"))
        assert not matcher.match(QueryBlock("cluster.ceph.node:wrong"))
        assert not matcher.match(QueryBlock("ceph.node:5aceb7fc"))
        assert not matcher.match(QueryBlock(".ceph.node:5aceb7fc"))
        assert not matcher.match(QueryBlock("...node:5aceb7fc"))
        assert not matcher.match(QueryBlock("ceph.cluster.node:5aceb7fc"))
        assert not matcher.match(QueryBlock("node.cluster.ceph:5aceb7fc"))

    def test_basic_data_by_multikey(self, matcher):
        """
        Match basic cdata by nested keys.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("key.innerkey.otherinnerkey:d:somevalue"))
        assert not matcher.match(QueryBlock("key.innerkey:d:somevalue"))

    def test_basic_dotted_key(self, matcher):
        """
        Test handling dotted keys.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("some-key:d:value"))
        assert matcher.match(QueryBlock("complex-path.with-nested.keys-here-there:d:value"))

    def test_basic_mixed_dotted_key(self, matcher):
        """
        Test handling dotted keys with the hyphens.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("mixed-name-key:d:value"))

    def test_basic_dotted_key_traits(self, matcher):
        """
        Test handling dotted keys in traits.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("ip-v4:10.10.10.10"))
        assert matcher.match(QueryBlock("ip-v4:10.10*"))
        assert matcher.match(QueryBlock("ip-v4:*"))
        assert matcher.match(QueryBlock("ip-v4:*.10"))
        assert matcher.match(QueryBlock("ip-v4:*10"))
        assert matcher.match(QueryBlock("ip-v4:*.*.*.*"))
        assert matcher.match(QueryBlock("ip-v4:r:(11|10)"))
        assert not matcher.match(QueryBlock("ip-v4:r:(11|12)"))
        assert matcher.match(QueryBlock("ip-v4:rx:(11|12)*"))

    def test_list_data_by_multikey(self, matcher):
        """
        Match list cdata by nested keys.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("key:d:value"))
        assert matcher.match(QueryBlock("key:d:othervalue"))
        assert matcher.match(QueryBlock("key.innerkey:d:innervalue"))

    def test_list_traits(self, matcher):
        """
        Test find if element is in the list.

        :param matcher:
        :return:
        """
        assert matcher.match(QueryBlock("items:1"))
        assert matcher.match(QueryBlock("items:2"))
        assert matcher.match(QueryBlock("items:3"))
        assert matcher.match(QueryBlock("items:4"))
        assert not matcher.match(QueryBlock("items:5"))
        assert not matcher.match(QueryBlock("items:0"))
