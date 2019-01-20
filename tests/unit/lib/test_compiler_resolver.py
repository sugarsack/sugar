# coding: utf-8
"""
Unit tests for compiler resolver.
"""
import os
import pytest
from mock import MagicMock, patch
from sugar.lib.compiler.objresolv import ObjectResolver
import sugar.lib.exceptions


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

    @patch("os.path.exists", MagicMock(return_value=True))
    @patch("os.makedirs", MagicMock())
    @patch("os.path.isdir", MagicMock(return_value=True))
    def test_resolve_init_by_uri(self):
        """
        Resolve init.st by URI, where path is pointing to the directory.

        :return: None
        """
        pth = "/opt/sugar"
        assert ObjectResolver(pth).resolve("foo.bar") == os.path.join(pth, "main/foo/bar/init.st")

    @patch("os.path.exists", MagicMock(return_value=True))
    @patch("os.makedirs", MagicMock())
    @patch("os.path.isdir", MagicMock(return_value=False))
    def test_resolve_file_by_uri(self):
        """
        Resolve state file path by URI, where path is pointing to a file.

        :return: None
        """
        pth = "/opt/sugar"
        assert ObjectResolver(pth).resolve("foo.bar") == os.path.join(pth, "main/foo/bar.st")

    @patch("os.path.exists", MagicMock(return_value=False))
    @patch("os.makedirs", MagicMock())
    @patch("os.path.isdir", MagicMock(return_value=False))
    def test_resolve_noexist_file_by_uri(self):
        """
        Resolve state file path by URI, where path is pointing to a file.
        The file doesn't exist, an Exception should be raised.

        :return: None
        """
        with pytest.raises(sugar.lib.exceptions.SugarSCResolverException) as exc:
            pth = "/opt/sugar"
            assert ObjectResolver(pth).resolve("foo.bar") == os.path.join(pth, "main/foo/bar.st")
        assert "State Compiler resolver error: No state files for URI 'foo.bar' has been found" in str(exc)

    @patch("os.path.exists", MagicMock(return_value=False))
    @patch("os.makedirs", MagicMock(side_effect=[OSError("Fatal error right in front of screen")]))
    @patch("os.path.isdir", MagicMock(return_value=False))
    def test_resolve_failure_initialise_env(self):
        """
        Failure initialise environment due to OSError
        that should be raised.

        :return: None
        """
        logmock = MagicMock()
        with pytest.raises(OSError) as exc, patch("sugar.lib.compiler.objresolv.get_logger", logmock) as lgr:
            pth = "/opt/sugar"
            assert ObjectResolver(pth).resolve("foo.bar") == os.path.join(pth, "main/foo/bar.st")
        assert "in front of screen" in str(exc)

        resolv_ref = logmock.call_args_list[0][0][0]

        assert isinstance(resolv_ref, ObjectResolver)
        assert resolv_ref.log.error.called

        msgpat, err_obj = resolv_ref.log.error.call_args_list[0][0]

        assert isinstance(err_obj, OSError)
        assert "Failure to initialise environment" in msgpat.format(err_obj)
