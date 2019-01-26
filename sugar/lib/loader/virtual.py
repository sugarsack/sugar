# coding: utf-8
"""
Module loader for virtual objects
"""
import os
import abc
import importlib

import sugar.lib.exceptions
from sugar.lib.loader.base import BaseModuleLoader


class VirtualModuleLoader(BaseModuleLoader):
    """
    Runner lazy loader class.
    """
    def _build_uri_map(self) -> None:
        """
        Build map.

        :return:
        """
        for w_pth, w_dirs, w_files in os.walk(self.modmap.root_path):
            if "_impl" in w_dirs:
                uri = self._get_module_uri(w_pth)
                self.modmap.map[uri] = None

    def _get_impl_class(self, mod):
        """
        Get implementation class from the runner module.

        :param mod: is the module to run
        :return: class
        """
        # Interface and Implementation classes
        ifce = cls = None

        mod = importlib.import_module(".".join([self.modmap._entrymod.__name__, mod]))
        ifaces_cnt = 0

        for c_name, c_obj in importlib.import_module(".".join([mod.__name__, "interface"])).__dict__.items():
            if isinstance(c_obj, abc.ABC) or isinstance(c_obj, abc.ABCMeta):
                ifaces_cnt += 1
                ifce = c_obj

        assert ifaces_cnt == 1, "Only one interface per module allowed. Found {}.".format(ifaces_cnt)

        impl = importlib.import_module(".".join([mod.__name__, "_impl"]))
        for implmod in os.listdir(os.path.dirname(impl.__file__)):
            implmod = implmod.split(".")[0]
            if implmod.startswith("_"):
                continue
            implmod = importlib.import_module("{}.{}".format(impl.__name__, implmod))
            for c_name, c_obj in implmod.__dict__.items():
                if c_name.startswith("_"):
                    continue
                try:
                    cls = c_obj()
                except TypeError as ex:
                    self.log.all("Assumed interface: {}", ex)
                except Exception as ex:
                    self.log.debug("Skipping '{}.{}': {}", implmod.__name__, c_name, ex)

        assert cls is not None, "No valid implementations has been found"

        return ifce, cls

    def _get_function(self, uri, *args, **kwargs):
        """
        Import module with the given function.

        :param uri:
        :return:
        """
        post_call = not bool(uri)
        uri = uri or ".".join(self._traverse_access_uri())
        mod, func = uri.rsplit(".", 1)
        if mod not in self.modmap.map:
            raise sugar.lib.exceptions.SugarLoaderException("Task {} not found".format(uri))
        cls = self.modmap.map[mod]
        if cls is None:
            ifce, cls = self._get_impl_class(mod)
            if func in cls.__class__.__dict__:
                if func not in ifce.__dict__:
                    raise sugar.lib.exceptions.SugarLoaderException(
                        "Access denied to function '{}'".format(func))
            else:
                raise sugar.lib.exceptions.SugarLoaderException(
                    "Function '{}' not found in module '{}'".format(func, mod))
            self.modmap.map[mod] = cls
        func = getattr(cls, func)

        return func(*args, **kwargs) if post_call else func
