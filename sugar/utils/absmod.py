# coding: utf-8
"""
Abstract module bases
"""
import json
from sugar.lib.traits import Traits
import sugar.modules.runners
import sugar.lib.exceptions


class ActionArray(list):
    """
    List with export to JSON
    """
    def to_json(self) -> str:
        """
        Export to JSON.

        :return: JSON string
        """
        return json.dumps(self)

    def from_json(self, data: str) -> None:
        """
        Import from json string
        :param data: json string
        :return: None
        """
        self.clear()
        self.extend(json.loads(data))


class ActionResult(dict):
    """
    Task status collector.
    """
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        self.__inf = ActionArray()
        self.__wrn = ActionArray()
        self.__err = ActionArray()
        self.errcode = 0

    @property
    def info(self) -> list:
        """
        Return info stream

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
        if isinstance(obj, str) and obj in self:
            self.__inf.extend(self.pop(obj))
        else:
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
        if isinstance(obj, str) and obj in self:
            self.__wrn.extend(self.pop(obj))
        else:
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
        If obj is a string, then it is a key of the self
        that will be transferred to the error stack.

        :param obj: Object for error
        :return: None
        """
        if isinstance(obj, str) and obj in self:
            self.__err.extend(self.pop(obj))
        else:
            self.__err.append(obj)

    def to_data(self) -> dict:
        """
        Export to data.

        :return: dictionary data
        """
        return {
            "module": dict(self),
            "log": {
                "info": self.info,
                "warn": self.warn,
                "error": self.error
            }
        }

    def to_json(self) -> str:
        """
        Export to JSON.

        :return: JSON serialised string
        """
        return json.dumps(dict(self))

    def from_json(self, data: str) -> None:
        """
        Import from JSON.

        :param data: JSON data string
        :return: None
        """
        self.update(json.loads(data))

    def set_run_response(self, response):
        """
        Sets runner response
        :param response:
        :return:
        """
        response.return_data = self.to_json()
        response.infos = self.info.to_json()
        response.warnings = self.warn.to_json()
        response.errors = self.error.to_json()

        return self


class BaseModule:
    """
    Base module.
    """
    def __init__(self):
        self.__traits = Traits()
        self.__modules = None  # virtual module lazy loader is injected on module load
        self.__validate__()

    def __validate__(self):
        """
        Validate this module. Override this method
        and raise an exception if the module is not valid.

        :returns None
        """

    @property
    def modules(self):
        """
        Modules loader.

        :returns VirtualModuleLoader
        """
        return self.__modules

    @modules.setter
    def modules(self, value):
        assert self.__modules is None, "Cannot reset module loader anymore"
        self.__modules = value

    @property
    def traits(self):
        """
        Traits map.

        :returns traits data
        """
        return self.__traits


class BaseRunnerModule(BaseModule):
    """
    Common class for runner modules.
    """

    @staticmethod
    def new_result():
        """
        Create a new action status

        :return: action result object
        """
        return ActionResult()


class BaseStateModule(BaseModule):
    """
    Common class for state modules.
    """

    @staticmethod
    def to_return(**data):
        """
        Format data for changes.

        changes:
          Changes diff

        comment:
          Message to the result

        warnings:
          List of warnings

        :param data: data of the returning container
        :raises SugarRuntimeException: if arguments has been missing found from the result object
        :return: Sugar return structure
        """
        missing = []
        for arg in ["changes", "comment", "warnings", "result"]:
            if arg not in data:
                if arg == "warnings":
                    data.setdefault(arg, [])
                elif arg == "comment":
                    data.setdefault(arg, "Success")
                elif arg == "changes":
                    data.setdefault(arg, {})
                else:
                    missing.append(arg)

        if missing:
            raise sugar.lib.exceptions.SugarRuntimeException(
                "Missing arguments for the result object: {}".format(", ".join(missing)))

        data = ActionResult(**data)
        data.warn = "warnings"

        return data
