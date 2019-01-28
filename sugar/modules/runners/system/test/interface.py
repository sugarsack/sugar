# coding: utf-8
"""
Interface to the module 'system.test'.
"""

import abc
from sugar.utils.absmod import BaseRunnerModule


class SysTestInterface(abc.ABC, BaseRunnerModule):
    """
    Interface of the system testing utilities
    """

    @abc.abstractmethod
    def ping(self, text: str = "pong") -> str:
        """
        Ping function.

        :param text: text for pinging
        :returns: string with the default text "pong"
        """
