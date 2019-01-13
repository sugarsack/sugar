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
