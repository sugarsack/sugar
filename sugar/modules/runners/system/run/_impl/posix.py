# coding: utf-8
"""
This is the description of your module.
Please make a better one.
"""
import os
import typing
import subprocess
from sugar.modules.runners.system.run.interface import RunInterface
from sugar.utils.absmod import ActionResult
from sugar.utils.stringutils import to_str


class RunModule(RunInterface):
    """
    Module description
    """
    STDOUT = "stdout"
    STDERR = "stderr"

    # Add another unix here (lowercase). Ban Windows as it should be different implementation instead.
    __platform__ = ["linux"]

    def spawn(self, command: str, args: typing.Union[list, str]) -> ActionResult:
        """
        Run an arbitrary command in a subprocess spawn via pipe.

        :param command: a command to run
        :param args: arguments
        :returns: tuple of STDOUT and STDERR
        """
        if isinstance(args, str):
            args = list(filter(None, args.split(" ")))

        result = self.new_result()
        stdout, stderr = subprocess.Popen([command] + args, stdout=subprocess.PIPE).communicate()
        result[self.STDOUT] = to_str(stdout or b"")
        result[self.STDERR] = to_str(stderr or b"")

        return result

    def spawn_list(self, command: str, args: typing.Union[list, str]) -> ActionResult:
        """
        Run an arbitrary command in a subprocess spawn via pipe where STDOUT and STDERR are lists.

        :param command: a command to run
        :param args: arguments
        :returns: tuple of STDOUT and STDERR
        """
        result = self.spawn(command=command, args=args)

        for section in [self.STDOUT, self.STDERR]:
            result[section] = result[section].split(os.linesep)

        return result

