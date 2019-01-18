# coding: utf-8
"""
Test sanitisers.
"""
import os
import sugar.utils.sanitisers


def mk_compat_path(*args) -> str:
    """
    Make a compatible path (Win, Unix)

    :param dirs: directory names
    :return: path
    """
    return os.path.sep.join([""] + list(args))


class TestSanitisers:
    """
    Test case for the sanitisers utilities.
    """
    def test_join_path(self):
        """
        Test path joined.

        :return: None
        """
        assert sugar.utils.sanitisers.join_path("foo", "bar") == mk_compat_path("foo", "bar")
