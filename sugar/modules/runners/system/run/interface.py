# coding: utf-8
"""
Interface to the module 'run'.
Please change this docstring for a better one.
"""
import abc
import typing
import platform
from sugar.utils.absmod import BaseRunnerModule, ActionResult


class RunInterface(abc.ABC, BaseRunnerModule):
    """
    Interface of the module 'run'.
    """

    __platform__ = []

    def __validate__(self) -> None:
        """
        Validate implementation of the module.

        :return:
        """
        assert platform.system().lower() in self.__platform__

    @abc.abstractmethod
    def spawn(self, command: str, args: list) -> ActionResult:
        """
        Run an arbitrary command in a subprocess spawn.

        :param command: a command to run
        :param args: list of parameters
        :returns: stdout and stderr slots in action result
        """

    @abc.abstractmethod
    def spawn_list(self, command: str, args: list) -> ActionResult:
        """
        Run an arbitrary command in a subprocess spawn, with stdout/stderr are lists.

        :param command: a command to run
        :param args: list of parameters
        :returns: stdout and stderr slots in action result
        """
