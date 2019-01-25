# coding: utf-8
"""
Abstract module bases
"""
from sugar.lib.traits import Traits
from sugar.lib.loader import RunnerModuleLoader
import sugar.modules.runners


class ActionResult(dict):
    """
    Task status collector.
    """
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        self.__inf = []
        self.__wrn = []
        self.__err = []
        self.errcode = 0

    @property
    def info(self) -> list:
        """
        Return infos stream

        :return: list
        """
        return self.__inf

    @info.setter
    def info(self, obj) -> None:
        """
        Collect an info.

        :param obj: an object for an info.
        :return: None
        """
        self.__inf.append(obj)

    @property
    def warn(self) -> list:
        """
        Return list of warnings.

        :return: list
        """
        return self.__wrn

    @warn.setter
    def warn(self, obj) -> None:
        """
        Collect a warning.

        :param obj: an object for a warning
        :return: None
        """
        self.__wrn.append(obj)

    @property
    def error(self) -> list:
        """
        Return list of errors.

        :return: list
        """
        return self.__err

    @error.setter
    def error(self, obj) -> None:
        """
        Add an error.

        :param obj: Object for error
        :return: None
        """
        self.__err.append(obj)


class BaseModule:
    """
    Base module
    """
    def __init__(self):
        self.__traits = Traits()

    @property
    def traits(self):
        """
        Traits map.
        """
        return self.__traits

    @staticmethod
    def new_result():
        """
        Create a new action status
        :return:
        """
        return ActionResult()


class BaseRunnerModule(BaseModule):
    """
    Common class for runner modules.
    """


class BaseStateModule(BaseModule):
    """
    Common class for state modules.
    """

    def __init__(self):
        BaseModule.__init__(self)
        self.__modules = RunnerModuleLoader(sugar.modules.runners)  # Map should be sigleton, so no rescan happens

    @property
    def modules(self):
        """
        Modules loader.
        """
        return self.__modules

    def to_return(self, **data):
        """
        Format data for changes.

        changes:
          Changes diff

        comment:
          Message to the result

        warnings:
          List of warnings

        :return:
        """
        missing = []
        for arg in ["changes", "comment", "warnings"]:
            if arg not in data:
                if arg == "warnings":
                    data.setdefault(arg, [])
                elif arg == "comment":
                    data.setdefault(arg, "Success")
                else:
                    missing.append(arg)

        if missing:
            raise sugar.lib.exceptions.SugarRuntimeException(
                "Missing arguments for the result object: {}".format(", ".join(missing)))

        data = ActionResult(**data)
        data.warn = "warnings"

        return data
