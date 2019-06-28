# coding: utf-8
"""
Loader utilities: decorators etc.
"""
import os
import builtins
import collections
import traceback

import sugar.utils.absmod
import sugar.lib.exceptions
import sugar.utils.files
from sugar.lib.compat import yaml
from sugar.lib.schemelib import Schema, And, Optional
from sugar.lib.logger.manager import get_logger


def guard(func):
    """
    Guard call.

    :param func: method or function to be guarded by the result object.
    :return: wrapper function
    """
    def caller(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            # TODO: Bug -- this returns ActionResult *also* when the module is trying to be imported.
            result = sugar.utils.absmod.ActionResult()
            result.error = str(exc)
            result.errcode = sugar.lib.exceptions.SugarException.get_errcode(exc)
            get_logger("EMERGENCY (loader guard)").error(traceback.format_exc())  # TODO: This is a temporary solution!
        return result

    return caller


class RunnerDataValidator:
    """
    Runner module data validator.
    Each runner has a schema of the output,
    which is validated on exit.
    """
    def __init__(self, mod):
        scheme_definition = os.path.join(os.path.dirname(mod.__file__), "scheme.yaml")
        with sugar.utils.files.fopen(scheme_definition) as sch:
            self.__raw_scheme = yaml.load(sch.read())
        self.__scheme = None
        self.__for_class = next(iter(self.__raw_scheme))
        self.__raw_scheme = self.__raw_scheme.pop(self.__for_class)

    @property
    def classname(self):
        """
        Classname of the scheme.

        :return: Name of the class
        """
        return self.__for_class

    @property
    def scheme(self):
        """
        Get scheme object.

        :return: Schema object
        """
        if self.__scheme is None:
            self.__scheme = collections.OrderedDict()
            for function in self.__raw_scheme:
                self.__scheme.setdefault(function, Schema(self._gen_scheme(self.__raw_scheme[function])))
            del self.__raw_scheme
        return self.__scheme

    def _gen_scheme(self, subtree, res=None):
        if res is None:
            res = {}
        for key, value in subtree.items():
            if isinstance(value, dict):
                res.update(self._gen_scheme(value, res=res))
            else:
                if key.startswith("r:"):
                    obj = And(key.split(":")[-1])
                else:
                    obj = Optional(key)
                obj_type = getattr(builtins, str(value))
                if obj_type is None:
                    raise sugar.lib.exceptions.SugarException("Unknown schema type: '{}'.".format(value))
                res[obj] = obj_type
        return res
