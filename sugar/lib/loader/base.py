# coding: utf-8
"""
Base abstract classes for the loader
"""
import os
import abc
import types

import sugar.lib.exceptions
from sugar.lib.logger.manager import get_logger
from sugar.lib.loader.util import guard
from sugar.utils.objects import Singleton


@Singleton
class ModuleMap:
    """
    Map scanner.
    """
    def __init__(self):
        self._uri_map = {}

    def map(self, id) -> dict:
        """
        URI map

        :return: dict of the uri map
        """
        try:
            _map = self._uri_map[id]
        except KeyError:
            _map = None
            self._uri_map.setdefault(id, {})

        return _map or self._uri_map[id]

    @property
    def build(self) -> bool:
        """
        Return True if modmap needs to be built

        :return: bool
        """
        return not bool(len(self._uri_map))


class BaseModuleLoader(abc.ABC):
    """
    Lazy loader class base.
    """

    def __init__(self, entrymod: types.ModuleType = None, filter_type=None):
        self.log = get_logger(self)
        self._id = "."
        self._parent = None
        self.__type__ = filter_type
        self._entrymod = entrymod
        if self._entrymod and not isinstance(self._entrymod, str):
            self.root_path = os.path.dirname(entrymod.__file__)
        else:
            self.root_path = None

        if self._entrymod is not None:
            self._modmap = ModuleMap()
            self._build_uri_map()

    def map(self):
        """
        Get map for the particular instance
        :return:
        """
        return self._modmap.map(getattr(self._entrymod, "__name__", self._entrymod))

    def _get_module_uri(self, path):
        """
        Get current module URI (the namespace).

        :param path: current module path.
        :return: uri
        """
        return ".".join([item for item in path[len(self.root_path):].split(os.path.sep) if item])

    def _traverse_access_uri(self, top=None, uri=None) -> list:
        """
        Traverse to URI what function is actually called.

        :return:
        """
        if uri is None:
            uri = []
        if top is None:
            top = self

        if top._parent is not None:
            self._traverse_access_uri(top._parent, uri)
        if top._id != ".":
            uri.append(top._id)

        return uri

    def __getattr__(self, item):
        obj = self.__class__()
        obj._parent = self
        obj._id = item
        obj._entrymod = self._entrymod
        obj._modmap = self._modmap

        return obj

    @guard
    def __getitem__(self, item):
        return self._get_function(item)

    def __call__(self, *args, **kwargs):
        """
        Get arbitrary function of any module.


        :param args: generic arguments for the function
        :param kwargs: generic keywords for the function
        :return: content of the loaded function
        """
        result = None

        try:
            result = self._get_function(None, *args, **kwargs)
        except Exception as exc:
            result.errcode = sugar.lib.exceptions.SugarException.get_errcode(exc=exc)
            result.errors.append(str(exc))

        return result

    @abc.abstractmethod
    def _build_uri_map(self):
        """
        Build URI map.

        :return: None
        """

    @abc.abstractmethod
    def _get_function(self, uri, *args, **kwargs):
        """
        Get function of the module.

        :param uri:
        :param args:
        :param kwargs:
        :return:
        """
