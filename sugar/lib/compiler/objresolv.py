# coding: utf-8
"""
Object resolver.

Purpose is to find a corresponding state
on the disk following the URI syntax.
"""

import os
import sugar.utils.sanitisers
from sugar.lib.logger.manager import get_logger


class ObjectResolver:
    """
    Resolve object by URI.
    Example:

        robj = ObjectResolver(path="/opt/sugar", env="main")
        path = robj.resolve("foo.bar")

    This should return "/opt/sugar/main/foo/bar.st" if "bar" is a file,
    and "/opt/sugar/main/foo/bar/init.st" if "bar" is a directory.
    """

    def __init__(self, path, env="main"):
        """
        Constructor.

        :param path: Path to the Sugar states root.
        :param env: Environment, which is just a sub-directory to the root.
        :raises OSError: if exist_ok is False
        """
        self.log = get_logger(self)
        self._path = sugar.utils.sanitisers.join_path(path, env)
        if not os.path.exists(self._path):
            try:
                os.makedirs(self._path)
            except OSError as ex:
                self.log.error("Failure to initialise environment: {}", ex)
                raise ex

    def resolve(self, url):
        """
        Resolve URI. The URI is dotted notation, where os.path.sep
        (slash or back-slash) is represented as "." (dot).

        :param url:
        :return: complete path to the state file.
        """
