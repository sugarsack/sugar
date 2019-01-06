"""
Unit test for keymanager.
"""
from __future__ import absolute_import, unicode_literals

import os
import pytest
from mock import MagicMock, patch, mock_open
from sugar.config import CurrentConfiguration
from tests.unit import data


@pytest.fixture
def default_master_configuration():
    """
    Default master configuration.

    :return: YAML
    """
    return open(os.path.join(os.path.dirname(data.__file__), "default_master.conf")).read()


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
    def test_config_loading(self, cfg_class, default_master_configuration):
        """
        Test configuration loading.

        :return: None
        """
        with patch("sugar.config.open", mock_open(read_data=default_master_configuration), create=True):
            inst = cfg_class("/path/to/config", {"foo": "bar"})
            assert inst.root.terminal.colors == 16
