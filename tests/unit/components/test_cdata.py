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
