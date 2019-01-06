"""
Unit test for keymanager.
"""
from __future__ import absolute_import, unicode_literals

import os
import pytest
from mock import MagicMock, patch, mock_open
from sugar.config import CurrentConfiguration
from tests.unit import data
from sugar.lib.schemelib import SchemaWrongKeyError


@pytest.fixture
def default_master_configuration():
    """
    Default master configuration.

    :return: YAML
    """
    return open(os.path.join(os.path.dirname(data.__file__), "default_master.conf")).read()


@pytest.fixture
def default_client_configuration():
    """
    Default client configuration.

    :return: YAML
    """
    return open(os.path.join(os.path.dirname(data.__file__), "default_client.conf")).read()


@pytest.fixture
def wrong_schema():
    """
    Return broken schema.

    :return: YAML
    """
    return "mad: max"


@pytest.fixture
def cfg_class():
    """
    Remove singleton instance after an initialisation.

    :return: CurrentConfiguration
    """
    CurrentConfiguration.__ref__ = None
    return CurrentConfiguration


class TestConfig(object):
    """
    Test config subsystem
    """
    @patch("sugar.config.get_current_component", MagicMock(return_value="master"))
    @patch("os.path.isfile", MagicMock(return_value=False))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_config_init(self, cfg_class):
        """
        Test configuration init.

        :return: None
        """
        isdir = MagicMock()
        with patch("os.path.isdir", isdir):
            inst = cfg_class("/path/to/config", {"foo": "bar"})
            assert isdir.call_args_list[0][0][0] == "/path/to/config"
            assert inst.DEFAULT_PATH == "/etc/sugar"

    @patch("sugar.config.get_current_component", MagicMock(return_value="master"))
    @patch("os.path.isfile", MagicMock(return_value=True))
    @patch("os.path.isdir", MagicMock(return_value=True))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_master_config_loading(self, cfg_class, default_master_configuration):
        """
        Test configuration loading.

        :return: None
        """
        with patch("sugar.config.open", mock_open(read_data=default_master_configuration), create=True):
            inst = cfg_class("/path/to/config", None)
            assert inst.root.terminal.colors == 16

    @patch("sugar.config.get_current_component", MagicMock(return_value="master"))
    @patch("os.path.isfile", MagicMock(return_value=True))
    @patch("os.path.isdir", MagicMock(return_value=True))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_master_config_schema_error(self, cfg_class, wrong_schema):
        """
        Test master wrong configuration loading.

        :return: None
        """
        with patch("sugar.config.open", mock_open(read_data=wrong_schema), create=True):
            with pytest.raises(SchemaWrongKeyError) as exc:
                cfg_class("/path/to/config", None)
            assert "Unexpected option 'mad'" in str(exc)

    @patch("sugar.config.get_current_component", MagicMock(return_value="client"))
    @patch("os.path.isfile", MagicMock(return_value=True))
    @patch("os.path.isdir", MagicMock(return_value=True))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_client_config_loading(self, cfg_class, default_client_configuration):
        """
        Test client configuration loading.

        :return: None
        """
        with patch("sugar.config.open", mock_open(read_data=default_client_configuration), create=True):
            inst = cfg_class("/path/to/config", None)
            assert inst.root.master[0].hostname == "127.0.0.1"

    @patch("sugar.config.get_current_component", MagicMock(return_value="client"))
    @patch("os.path.isfile", MagicMock(return_value=True))
    @patch("os.path.isdir", MagicMock(return_value=True))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_client_config_schema_error(self, cfg_class, wrong_schema):
        """
        Test client wrong configuration loading. Should raise a SchemaWrongKeyError.

        :return: None
        """
        with patch("sugar.config.open", mock_open(read_data=wrong_schema), create=True):
            with pytest.raises(SchemaWrongKeyError) as exc:
                cfg_class("/path/to/config", None)
            assert "Unexpected option 'mad'" in str(exc)

    @patch("sugar.config.get_current_component", MagicMock(return_value="master"))
    @patch("os.path.isfile", MagicMock(return_value=True))
    @patch("os.path.isdir", MagicMock(return_value=True))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test__config_log_level(self, cfg_class, default_master_configuration, default_client_configuration):
        """
        Test log level configuration

        :return: None
        """
        class _Opts(object):
            log_level = "no_idea"

        with patch("sugar.config.open", mock_open(read_data=default_master_configuration), create=True):
            inst = cfg_class("/path/to/config", _Opts())
            assert inst.root.log[0].level == _Opts.log_level

        with patch("sugar.config.open", mock_open(read_data=default_client_configuration), create=True):
            inst = cfg_class("/path/to/config", _Opts())
            assert inst.root.log[0].level == _Opts.log_level
