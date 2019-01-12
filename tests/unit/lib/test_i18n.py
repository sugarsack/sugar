# coding: utf-8
"""
Test i18n class
"""
from __future__ import unicode_literals, absolute_import
from mock import MagicMock, patch, mock_open
import pytest
import sugar.lib.i18n


@pytest.fixture
def gettext_class():
    """
    Singleton-free class.

    :return: GetText instance
    """
    sugar.lib.i18n.GetText.__ref__ = None
    return sugar.lib.i18n.GetText


class TestGetText(object):
    """
    Test case for the GetText
    """
    @patch("os.path.join", MagicMock(return_value="/in/the/middle/of/nowhere"))
    @patch("os.path.exists", MagicMock(return_value=True))
    def test_internal_format(self, gettext_class):
        """
        Test internal format and the structure within the YAML i18n messages.
        :return: None
        """
        translation_data = """
apple:
  none: no apples
  one: one apple
  few: few apples
  many: lots of apples
        """.strip()
        with patch("sugar.utils.files.fopen", mock_open(read_data=translation_data), create=True):
            gtx = gettext_class()
            assert gtx.gettext("apple") == "no apples"
        assert gtx.gettext("apple", 1) == "one apple"
        assert gtx.gettext("apple", 2) == "few apples"
        assert gtx.gettext("apple", 4) == "lots of apples"

    @patch("os.path.join", MagicMock(return_value="/in/the/middle/of/nowhere"))
    @patch("os.path.exists", MagicMock(return_value=True))
    @patch("os.access", MagicMock(return_value=True))
    def test_autoadd_data(self, gettext_class):
        """
        Test auto-add message to the translation.

        :return: None
        """
        msg = "Homer Simpson"
        yaml_mock = MagicMock()
        with patch("sugar.utils.files.fopen", mock_open(read_data=""),
                   create=True) as fhm, patch("yaml.dump", yaml_mock) as yml:
            gtx = gettext_class()
            for count in [0, 1, 3, 4]:
                gtx.gettext(msg, count=count)

            assert yaml_mock.called
            translation_entry = yaml_mock.call_args_list[0][0][0]
            assert msg in translation_entry
            plurals = translation_entry[msg]
            assert plurals["none"] == plurals["one"] == plurals["few"] == plurals["many"] == msg
