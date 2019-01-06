"""
Unit test for keymanager.
"""
from __future__ import absolute_import, unicode_literals

from mock import MagicMock, patch
from sugar.config import CurrentConfiguration


class TestConfig(object):
    """
    Test config subsystem
    """

    @patch("sugar.config.get_current_component", MagicMock(return_value="master"))
    @patch("os.path.isfile", MagicMock(return_value=False))
    @patch("os.path.expanduser", MagicMock(return_value="/path/to/sugar"))
    def test_config_init(self):
        """
        Test configuration init.

        :return: None
        """
        isdir = MagicMock()
        dirs = {"/path/to/config": None, "/path/to/sugar/.sugar": None, "/etc/sugar": None}
        with patch("os.path.isdir", isdir):
            inst = CurrentConfiguration("/path/to/config", {"foo": "bar"})
            print()
            for arglist in isdir.call_args_list:
                assert arglist[0][0] in dirs
                del dirs[arglist[0][0]]
            assert not dirs
            assert inst.DEFAULT_PATH == "/etc/sugar"
