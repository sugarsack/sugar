# coding: utf-8
"""
Unit tests for compiler tree.
"""

import os
import pytest

from sugar.lib.compiler.objtree import ObjectTree
from sugar.lib.compiler.objresolv import ObjectResolver
import tests.integration
from sugar.lib.outputters.console import MappingOutput


@pytest.fixture
def get_states_root():
    """
    Get states root (default env).

    :return: path to the states root.
    """
    return os.path.join(os.path.dirname(tests.integration.__file__), "root", "states")


class TestCompilerTree:
    """
    Tree compiler test case.
    """
    def test_load_main_state(self, get_states_root):
        """
        Test loading main state (main.st) implicitly.

        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_states_root))
        otree.load()

        assert list(otree.tree.keys()) == ['pyssl', 'ssh_configuration', 'httpd_installed']
        assert otree.tree["ssh_configuration"]["pkg.installed"]["pkgs"][0] == "openssh-server"

    def test_load_main_state_explicitly(self, get_states_root):
        """
        Test loading main state (main.st) explicitly.

        :return: None
        """

        otree = ObjectTree(ObjectResolver(get_states_root))
        otree.load("main")

        assert list(otree.tree.keys()) == ['pyssl', 'ssh_configuration', 'httpd_installed']
        assert otree.tree["ssh_configuration"]["pkg.installed"]["pkgs"][0] == "openssh-server"

    def test_load_templated_state(self, get_states_root):
        """
        Test loading templated state.

        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_states_root))
        otree.load("dynamic")
        assert "enumerate" in otree.tree
        assert otree.tree["enumerate"] == ['echo "1"', 'echo "2"', 'echo "3"']

    def test_load_subset_by_uri(self, get_states_root):
        """
        Test loading templated state by uri subset.

        :return:
        """
        otree = ObjectTree(ObjectResolver(get_states_root))
        otree.load("services.ssl")
        assert len(otree.tree) == 1
        assert "pyssl" in otree.tree
        assert otree.tree["pyssl"]["file"][0]["managed"]["name"] == "/etc/ssl.conf"
