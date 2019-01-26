# coding: utf-8
"""
Interface to the module 'system.test'.
"""

import abc
import platform
from sugar.utils.absmod import BaseRunnerModule


class SysTestInterface(abc.ABC, BaseRunnerModule):
    """
    Interface of the system testing utilities
    """

    @abc.abstractmethod
    def ping(self, name:str = "pong") -> str:
        """
        Ping fuction.

        :returns: string with the default text "pong"
        """
