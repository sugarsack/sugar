# coding: utf-8
"""
This is the description of your module.
Please make a better one.
"""
import typing
from sugar.modules.runners.system.run.interface import RunInterface


class RunModule(RunInterface):
    """
    Module description
    """

    # Add another unix here (lowercase). Ban Windows as it should be different implementation instead.
    __platform__ = ["linux"]

    def spawn(self, command: str) -> typing.Tuple[str, str]:
        """
        Run an arbitrary command in a subprocess spawn.

        :param command: a command to run
        :returns: tuple of STDOUT and STDERR
        """

        result = self.new_result()
        result["stdout"] = ""
        result["stderr"] = ""

        return result
