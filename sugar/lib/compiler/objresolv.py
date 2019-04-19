# coding: utf-8
"""
Object resolver.

Purpose is to find a corresponding state
on the disk following the URI syntax.
"""

import os
import typing
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
    DEFAULT_ENV = "main"

    def __init__(self, path, env=None):
        """
        Constructor.

        :param path: Path to the Sugar states root.
        :param env: Environment, which is just a sub-directory to the root.
        :raises OSError: if exist_ok is False
        """
        self.__callbacks = {"uri_error": []}
        if not env:
            env = self.DEFAULT_ENV

        self.log = get_logger(self)
        self.__path = sugar.utils.sanitisers.join_path(path, env).rstrip(os.path.sep)
        if self.__path == path:
            self.__path = sugar.utils.sanitisers.join_path(path, self.DEFAULT_ENV).rstrip(os.path.sep)
        if not os.path.exists(self.__path):
            try:
                os.makedirs(self.__path)
            except OSError as ex:
                self.log.error("Failure to initialise environment: {}", ex)
                raise ex
        self.__main_path = None

    @property
    def path(self):
        """
        Root path for the states.

        :return: absolute path.
        """
        return self.__path

    def get_main(self):
        """
        Get state main.st (top).

        :return: Path to main.st if needed.
        """
        if self.__main_path is None:
            for item in os.walk(self.__path):
                pth, _, files = item
                if self.TOP_STATE in files:
                    self.__main_path = os.path.join(pth, self.TOP_STATE)
                    break

        return self.__main_path

    def get_resource_path(self, subpath):
        """
        Get resource. If this is a directory, this should append an "init.st".

        :param subpath: subpath after the URI
        :raises SugarSCResolverException: raised when no states found by the given URI.
        :return: Full path to the resource.
        """
        _path = os.path.join(self.__path, subpath)
        if os.path.isdir(_path):
            _path = os.path.join(_path, self.INIT_STATE)
        else:
            _path = "{}.st".format(_path)
            if not os.path.exists(_path):
                uri = self.subpath_to_uri(subpath)
                self._on_callbacks("uri_error", path=_path, uri=uri)
                raise sugar.lib.exceptions.SugarSCResolverException(
                    "No state files for URI '{}' has been found".format(uri))

        return _path

    @staticmethod
    def subpath_to_uri(subpath):
        """
        Converts subpath to URI.

        :param subpath: Relative path to the state.
        :return: URI
        """
        path = []
        for node in subpath.split(os.path.sep):
            path.append(node.split(".")[0])

        return ".".join(path)

    @staticmethod
    def uri_to_subpath(uri):
        """
        Converts URI to subpath.

        :param uri: URI to the state
        :return: subpath
        """
        return sugar.utils.sanitisers.join_path(*uri.split("."), relative=True)

    def resolve(self, uri=None):
        """
        Resolve URI. The URI is dotted notation, where os.path.sep
        (slash or back-slash) is represented as "." (dot). If uri
        parameter is None, then path to the top file is returned.

        :param uri: Dot-notated URI for specific state, None for getting main.
        :return: complete path to the state file.
        """
        return self.get_main() if uri is None else self.get_resource_path(self.uri_to_subpath(uri))

    def on_uri_error(self, callback: typing.Callable) -> typing.ClassVar:
        """
        Add callback on URI error.

        :param callback: function
        :return: return of the callback
        """
        self.__callbacks["uri_error"].append(callback)
        return self

    def _on_callbacks(self, section, *args, **kwargs) -> None:
        """
        Call corresponding callbacks.

        :param section: registered callbacks.
        :param args: args for each callback
        :param kwargs: kwargs for each callback
        :return: None
        """
        for callback in self.__callbacks.get(section, []):
            callback(*args, **kwargs)
