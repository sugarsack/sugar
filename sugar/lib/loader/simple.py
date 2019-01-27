# coding: utf-8
"""
Module loader for simple objects
"""
import os
import importlib

import sugar.lib.exceptions
from sugar.lib.loader.base import BaseModuleLoader


class SimpleModuleLoader(BaseModuleLoader):
    """
    Loader for simple architecture modules that has
    no interface and has no multiple implementations.
    """
    def _build_uri_map(self) -> None:
        """
        Build URI map.
m
        :return:
        """
        for w_pth, w_dirs, w_files in os.walk(self.root_path):
            if all([fname in w_files for fname in ["doc.yaml", "examples.yaml", "__init__.py"]]):
                uri = self._get_module_uri(w_pth)
                self.map()[uri] = None

    def _get_function(self, uri, *args, **kwargs):
        """
        Import module with the given function.

        :param uri:
        :return:
        """
        call = not bool(uri)
        uri = uri or ".".join(self._traverse_access_uri())
        mod, func = uri.rsplit(".", 1)
        if mod not in self.map():
            raise sugar.lib.exceptions.SugarLoaderException("Task {} not found".format(uri))

        cls = self.map()[mod]
        if cls is None:
            uri = "{}.{}".format(self._entrymod.__name__, mod)
            cls = getattr(importlib.import_module(uri), "__init__", None)
            assert cls is not None, ("Implementation class was not found. "
                                     "Module '{}' should export it as '__init__'".format(mod))

            self.map()[mod] = cls()
        assert func in self.map()[mod].__class__.__dict__, "Function '{}' not found in module '{}'".format(func, mod)
        func = getattr(self.map()[mod], func)

        return func(*args, **kwargs) if call else func
