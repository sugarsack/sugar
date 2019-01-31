# coding: utf-8
"""
Module loader for virtual objects
"""
import os
import abc
import importlib

import sugar.lib.exceptions
from sugar.lib.loader.base import BaseModuleLoader
from sugar.lib.loader.util import RunnerDataValidator


class VirtualModuleLoader(BaseModuleLoader):
    """
    Runner lazy loader class.
    """
    def _build_uri_map(self) -> None:
        """
        Build map.

        :return:
        """
        for w_pth, w_dirs, w_files in os.walk(self.root_path):  # pylint:disable=W0612
            if "_impl" in w_dirs:
                uri = self._get_module_uri(w_pth)
                self.map()[uri] = None

    def _get_impl_class(self, mod):
        """
        Get implementation class from the runner module.

        :param mod: is the module to run
        :return: class
        """
        # Interface and Implementation classes
        ifce = cls = None

        mod = importlib.import_module(".".join([self._entrymod.__name__, mod]))
        ifaces_cnt = 0

        for c_name, c_obj in importlib.import_module(".".join([mod.__name__, "interface"])).__dict__.items():
            if isinstance(c_obj, (abc.ABC, abc.ABCMeta)):
                ifaces_cnt += 1
                ifce = c_obj

        assert ifaces_cnt == 1, "Only one interface per module allowed. Found {}.".format(ifaces_cnt)

        rdv_obj = RunnerDataValidator(mod)
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
        assert ifce.__name__ == rdv_obj.classname, ("Data output scheme '{}' is not for the "
                                                    "module interface '{}'".format(rdv_obj.classname, ifce.__name__))
        cls.scheme = rdv_obj.scheme
        return ifce, cls

    def _get_function(self, uri, *args, **kwargs):
        """
        Import module with the given function.

        :param uri: URI of the function (or None)
        :raises SugarLoaderException: if task was not found,
                                      access denied to the function or function was not found
        :return: function
        """
        post_call = not bool(uri)
        uri = uri or ".".join(self._traverse_access_uri())
        mod, func = uri.rsplit(".", 1)
        if mod not in self.map():
            raise sugar.lib.exceptions.SugarLoaderException("Task {} not found".format(uri))
        cls = self.map()[mod]
        if cls is None:
            ifce, cls = self._get_impl_class(mod)
            cls.modules = self
            self.map()[mod] = cls
            if func in cls.__class__.__dict__:
                if func not in ifce.__dict__:
                    raise sugar.lib.exceptions.SugarLoaderException(
                        "Access denied to function '{}'".format(func))
            else:
                raise sugar.lib.exceptions.SugarLoaderException(
                    "Function '{}' not found in module '{}'".format(func, mod))
        _func_or_data = getattr(cls, func)

        if post_call:
            result = _func_or_data(*args, **kwargs)
            cls.scheme[func].validate(result)
        else:

            def defer_to_call(*args, **kwargs):
                """
                Defer bound method for a post-call for validation.

                :param args: generic arguments
                :param kwargs: generic keywords
                :return: generic object
                """
                data = _func_or_data(*args, **kwargs)
                cls.scheme[func].validate(data)
                return data
            result = defer_to_call

        return result
