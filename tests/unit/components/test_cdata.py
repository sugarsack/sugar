# config: utf-8
"""
Test client data matchers
"""
import pytest

from sugar.lib.compat import yaml
from sugar.components.server.cdatamatch import UniformMatch
from sugar.components.server.cdatastore import CDataContainer
from sugar.components.server.query import QueryBlock


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
    """
    cnt = CDataContainer("han-solo")
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
        }
    cnt.inherencies = yaml.load(data)

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
