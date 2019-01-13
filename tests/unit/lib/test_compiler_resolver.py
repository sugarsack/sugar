# coding: utf-8
"""
Unit tests for compiler resolver.
"""
from sugar.lib.compiler.objresolv import ObjectResolver
from mock import MagicMock, patch
import os


class TestCompilerResolver:
    """
    Unit tests for compiler resolver.
    """

    @patch("os.path.exists", MagicMock(return_value=True))
    @patch("os.makedirs", MagicMock())
    def test_path_environments(self):
        """
        Resolve environment paths.

        :return: None
        """
        pth = "/opt/sugar"

        resolver = ObjectResolver(pth, "uat")
        assert resolver.path == os.path.join(pth, "uat")

        resolver = ObjectResolver(pth, "../../../../../../../etc")
        assert resolver.path == os.path.join(pth, "etc")

        for env in ["\\\\\\\\\\\\\\\\\\\\\n", "\n\t  \n", None, "main", "../../../../../../../"]:
            assert ObjectResolver(pth, env).path == os.path.join(pth, "main")

    @patch("os.path.exists", MagicMock(return_value=True))
    @patch("os.makedirs", MagicMock())
    @patch("os.walk", MagicMock(return_value=[
        ("/opt/sugar", ["foo", "bar"], ["init.st"]),
        ("/opt/sugar/foo", [], ["bar.st"]),
        ("/opt/sugar/somewhere", ["theris"], ["main.st"]),
    ]))
    def test_resolve_main_by_uri(self):
        """
        Resolve main.st when nothing is specified.

        :return: None
        """
        pth = "/opt/sugar"
        assert ObjectResolver(pth).resolve() == os.path.join(pth, "somewhere/main.st")


    def test_resolve_init_by_uri(self):
        """
        Resolve init.st by URI.

        :return: None
        """

    def test_resolve_file_by_uri(self):
        """
        Resolve state file path by URI.

        :return:
        """
