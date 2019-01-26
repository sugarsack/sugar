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

        :return:
        """
        for w_pth, w_dirs, w_files in os.walk(self.modmap.root_path):
            if all([fname in w_files for fname in ["doc.yaml", "examples.yaml", "__init__.py"]]):
                uri = self._get_module_uri(w_pth)
                self.modmap.map[uri] = None

    def _get_function(self, uri, *args, **kwargs):
        """
        Import module with the given function.

        :param uri:
        :return:
        """
        uri = uri or ".".join(self._traverse_access_uri())
        mod, func = uri.rsplit(".", 1)
        if mod not in self.modmap.map:
            raise sugar.lib.exceptions.SugarLoaderException("Task {} not found".format(uri))

        cls = self.modmap.map[mod]
        if cls is None:
            cls = getattr(importlib.import_module("{}.{}".format(self.modmap._entrymod.__name__, mod)), "__init__", None)
            assert cls is not None, ("Implementation class was not found. "
                                     "Module '{}' should export it as '__init__'".format(mod))
            self.modmap.map[mod] = cls()
        assert func in self.modmap.map[mod].__class__.__dict__, "Function '{}' not found in module '{}'".format(func, mod)

        return getattr(self.modmap.map[mod], func)
