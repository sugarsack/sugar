# coding: utf-8
"""
Module loader for custom objects.
"""
import os
import importlib.util
from sugar.lib.loader.base import BaseModuleLoader


class CustomModuleLoader(BaseModuleLoader):
    """
    Custom user modules. They are very simple functions,
    just like Ansible or Salt modules.
    """
    def __init__(self, *paths, filter_type=None):
        self.paths = paths
        BaseModuleLoader.__init__(self, entrymod="sugar.modules.custom", filter_type=filter_type)

    def _build_uri_map(self):
        """
        Build URI map.

        :return: None
        """
        for path in self.paths:
            for w_pth, w_dirs, w_files in os.walk(path):  # pylint:disable=W0612
                mod = [item for item in (w_pth[len(path):] or '').split(os.path.sep) if item]
                for w_file in w_files:
                    if w_file.endswith(".py"):
                        mod.append(w_file.split(".")[0])
                        self.map().setdefault('.'.join(mod), os.path.join(w_pth, w_file))

    def _get_function(self, uri, *args, **kwargs):
        """
        Get function of the module.

        :param uri:
        :param args:
        :param kwargs:
        :return:
        """
        call = bool(not uri)
        uri = uri or ".".join(self._traverse_access_uri())
        mod, func = uri.rsplit(".", 1)
        src = self.map()[mod]
        if isinstance(src, str) and os.path.exists(src):
            src = importlib.util.spec_from_file_location(mod, src)
            self.map()[mod] = importlib.util.module_from_spec(src)
            src.loader.exec_module(self.map()[mod])
            src = self.map()[mod]
        func = getattr(src, func)

        return func(*args, **kwargs) if call else func
