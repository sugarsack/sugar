# coding: utf-8
"""
Object resolver.

Purpose is to find a corresponding state
on the disk following the URI syntax.
"""

import os
import sugar.utils.sanitisers
from sugar.lib.logger.manager import get_logger
import sugar.lib.exceptions


class ObjectResolver:
    """
    Resolve object by URI.
    Example:

        robj = ObjectResolver(path="/opt/sugar", env="main")
        path = robj.resolve("foo.bar")

    This should return "/opt/sugar/main/foo/bar.st" if "bar" is a file,
    and "/opt/sugar/main/foo/bar/init.st" if "bar" is a directory.

    Rules:
      - Works only with one environment.
      - Only one "main.st" per environment.
      - URI that references directory is prepended with "init.st" file.
    """

    INIT_STATE = "init.st"
    TOP_STATE = "main.st"

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
        self.__main_path = None

    def get_main(self):
        """
        Get state main.st (top).

        :return: Path to main.st if needed.
        """
        if self.__main_path is None:
            for item in os.walk(self._path):
                pth, dirs, files = item
                if self.TOP_STATE in files:
                    self.__main_path = os.path.join(pth, self.TOP_STATE)
                    break

        return self.__main_path

    def get_resource_path(self, subpath):
        """
        Get resource. If this is a directory, this should append an "init.st".

        :param subpath: subpath after the URI
        :return: Full path to the resource.
        """
        _path = os.path.join(self._path, subpath)
        if os.path.isdir(_path):
            _path = os.path.join(_path, self.INIT_STATE)
        else:
            _path = "{}.st".format(_path)
            if not os.path.exists(_path):
                raise sugar.lib.exceptions.SugarSCResolverException(
                    "No state files for URI '{}' has been found".format(self.subpath_to_uri(subpath)))

        return _path

    @staticmethod
    def subpath_to_uri(subpath):
        """
        Converts subpath to URI.

        :param subpath:
        :return:
        """
        return ".".join(subpath.split(os.path.sep))

    @staticmethod
    def uri_to_subpath(uri):
        """
        Converts URI to subpath.

        :param uri:
        :return:
        """
        return sugar.utils.sanitisers.join_path(*uri.split("."), relative=True)

        """
        Resolve URI. The URI is dotted notation, where os.path.sep
        (slash or back-slash) is represented as "." (dot).

        :param url:
        :return: complete path to the state file.
        """
