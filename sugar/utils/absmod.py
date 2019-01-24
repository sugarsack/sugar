# coding: utf-8
"""
Abstract module bases
"""
from sugar.lib.traits import Traits
from sugar.lib.loader import RunnerModuleLoader
import sugar.modules.runners


class BaseStateModule:
    """
    Common class for state modules.
    """
    def __init__(self):
        self.__traits = Traits()
        self.__modules = RunnerModuleLoader(sugar.modules.runners)  # Map should be sigleton, so no rescan happens

    @property
    def traits(self):
        """
        Traits map.
        """
        return self.__traits

    @property
    def modules(self):
        """
        Modules loader.
        """
        return self.__modules
