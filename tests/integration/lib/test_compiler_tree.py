# coding: utf-8
"""
Unit tests for compiler tree.
"""

import os
import pytest

from sugar.lib.compiler.objtree import ObjectTree
from sugar.lib.compiler.objresolv import ObjectResolver
from sugar.lib.compat import yaml
import sugar.lib.exceptions

import tests.integration


@pytest.fixture
def get_barestates_root():
    """
    Get states root (default env).

    :return: path to the states root.
    """
    return os.path.join(os.path.dirname(tests.integration.__file__), "root", "barestates")


class TestCompilerTree:
    """
    Tree compiler test case.
    """
    def test_load_main_state(self, get_barestates_root):
        """
        Test loading main state (main.st) implicitly.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_barestates_root)).load()

        assert list(otree.tree.keys()) == ['pyssl', 'ssh_configuration', 'httpd_installed']
        assert otree.tree["ssh_configuration"]["pkg.installed"]["pkgs"][0] == "openssh-server"

    def test_load_main_state_explicitly(self, get_barestates_root):
        """
        Test loading main state (main.st) explicitly.

        :param get_barestates_root: states root fixture function
        :return: None
        """

        otree = ObjectTree(ObjectResolver(get_barestates_root)).load("main")

        assert list(otree.tree.keys()) == ['pyssl', 'ssh_configuration', 'httpd_installed']
        assert otree.tree["ssh_configuration"]["pkg.installed"]["pkgs"][0] == "openssh-server"

    def test_load_templated_state(self, get_barestates_root):
        """
        Test loading templated state.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_barestates_root)).load("dynamic")
        assert "enumerate" in otree.tree
        assert otree.tree["enumerate"] == ['echo "1"', 'echo "2"', 'echo "3"']

    def test_load_subset_by_uri(self, get_barestates_root):
        """
        Test loading templated state by uri subset.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_barestates_root)).load("services.ssl")
        assert len(otree.tree) == 1
        assert "pyssl" in otree.tree
        assert otree.tree["pyssl"]["file"][0]["managed"]["name"] == "/etc/ssl.conf"

    def test_faulty_yaml_syntax(self, get_barestates_root):
        """
        Test an exception raises when resolving faulty YAML syntax.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        with pytest.raises(yaml.scanner.ScannerError) as exc:
            ObjectTree(ObjectResolver(get_barestates_root)).load("faulty_yaml_syntax")

        assert "mapping values are not allowed here" in str(exc)

    def test_multiple_excludes(self, get_barestates_root):
        """
        Test multiple excludes in different state files.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        otree = ObjectTree(ObjectResolver(get_barestates_root)).load("inheritance.overlay")

        # Multiple exclusions
        assert "statement_one" not in otree.tree
        assert "statement_two" not in otree.tree
        assert "statement_three" in otree.tree
        assert "statement_four" in otree.tree
        assert len(otree.tree) == 2

        # Order is kept
        three, four = list(otree.tree.keys())
        assert three == "statement_three"
        assert four == "statement_four"

    def test_jinja_syntax_broken(self, get_barestates_root):
        """
        Test broken Jinja2 syntax.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        with pytest.raises(sugar.lib.exceptions.SugarSCException) as exc:
            ObjectTree(ObjectResolver(get_barestates_root)).load("faulty_jinja_syntax")
        assert "State Compiler error" in str(exc)

    def test_empty_state(self, get_barestates_root):
        """
        Test empty state is not breaking compiler.

        :param get_barestates_root: states root fixture function
        :return: None
        """
        assert not bool(ObjectTree(ObjectResolver(get_barestates_root)).load("null").tree)
