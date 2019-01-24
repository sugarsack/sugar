# coding: utf-8
"""
Abstract module bases
"""
from sugar.lib.traits import Traits
from sugar.lib.loader import RunnerModuleLoader
from sugar.transport import RunnerModulesMsgFactory, StateModulesMsgFactory

import sugar.modules.runners


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
    def get_return():
        raise NotImplementedError("Not implemented")


class BaseRunnerModule(BaseModule):
    """
    Common class for runner modules.
    """

    @staticmethod
    def get_return():
        """
        Create a return object instance
        """
        return RunnerModulesMsgFactory.create()


class BaseStateModule(BaseModule):
    """
    Common class for state modules.
    """

    def __init__(self):
        BaseModule.__init__(self)
        self.__modules = RunnerModuleLoader(sugar.modules.runners)  # Map should be sigleton, so no rescan happens

    @staticmethod
    def get_return():
        """
        Create a return object instance
        """
        return StateModulesMsgFactory.create()

    @property
    def modules(self):
        """
        Modules loader.
        """
        return self.__modules
