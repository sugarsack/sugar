# coding: utf-8
"""
Module lazy loader.
Key features:

 - Black-list support. Some things should not be lazy loaded.
 - Load on access demand.
"""
import os
import abc
import types
import importlib
from sugar.lib.logger.manager import get_logger
import sugar.lib.exceptions
import sugar.modules.runners
import sugar.modules.states
import sugar.utils.absmod


def guard(func):
    """
    Guard call.

    :param func: method or function to be
    guarded by the result object.

    :return: wrapper function
    """
    def caller(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            result = sugar.utils.absmod.ActionResult()
            result.error = str(exc)
            result.errcode = sugar.lib.exceptions.SugarException.get_errcode(exc)
        return result

    return caller


class RunnerModuleLoader:
    """
    Lazy loader class.
    """

    def __init__(self, entrymod: types.ModuleType = None):
        self.log = get_logger(self)
        self._id = "."
        self._parent = None

        if entrymod:
            self._root_path = os.path.dirname(entrymod.__file__)
            self._entrymod = entrymod
            self._uri_map = None
            self._build_uri_map()

    def _get_module_uri(self, path):
        """
        Get current module URI (the namespace).

        :param path: current module path.
        :return: uri
        """
        return ".".join([item for item in path[len(self._root_path):].split(os.path.sep) if item])

    def _build_uri_map(self) -> None:
        """
        Build map.

        :return:
        """
        self._uri_map = {}
        for w_pth, w_dirs, w_files in os.walk(self._root_path):
            if "_impl" in w_dirs:
                uri = self._get_module_uri(w_pth)
                self._uri_map[uri] = None

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
        if mod not in self._uri_map:
            raise sugar.lib.exceptions.SugarLoaderException("Task {} not found".format(uri))
        cls = self._uri_map[mod]
        if cls is None:
            ifce, cls = self._get_impl_class(mod)
            if func in cls.__class__.__dict__:
                if func not in ifce.__dict__:
                    raise sugar.lib.exceptions.SugarLoaderException("Access denied to function '{}'".format(func))
            else:
                raise sugar.lib.exceptions.SugarLoaderException("Function '{}' not found in module '{}'".format(func, mod))
            self._uri_map[mod] = cls
        func = getattr(cls, func)

        return func(*args, **kwargs) if post_call else func

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

        # reference pointers from parent
        obj._uri_map = self._uri_map
        obj._entrymod = self._entrymod

        return obj

    @guard
    def __getitem__(self, item):
        return self._get_function(item)

    def __call__(self, *args, **kwargs):
        """
        Get arbitrary function of any module.

        Accepts named parameter "uri" or first positional value
        is an uri, if this object is called at root. In this case
        it will resolve module and target by an uri.

        :param args: generic arguments for the function
        :param kwargs: generic keywords for the function
        :raises
        :return: content of the loaded function
        """
        result = None

        try:
            result = self._get_function(None, *args, **kwargs)
        except Exception as exc:
            result.errcode = sugar.lib.exceptions.SugarException.get_errcode(exc=exc)
            result.errors.append(str(exc))

        return result


class StateModuleLoader:
    """
    States module loader.
    """
    def __init__(self, entrymod: types.ModuleType = None):
        self.entrymod = entrymod


class CustomModuleLoader:
    """
    Custom user modules. They are very simple functions,
    just like Ansible or Salt modules.
    """
    def __init__(self, *paths):
        self.paths = paths


class SugarModuleLoader:
    """
    Sugar module loader.
    """
    def __init__(self, *paths):
        self.runners = RunnerModuleLoader(sugar.modules.runners)
        self.states = StateModuleLoader(sugar.modules.states)
        self.custom = CustomModuleLoader(*paths)

