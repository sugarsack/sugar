"""
Backslashes are ugly. Use only when it is only syntactically
necessary (multiple "with" statement, for example).
"""

import os

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class BackslashChecker(checkers.BaseChecker):
    """
    Backslashes are just plain ugly. Please use them only when you must.
    Otherwise avoid them.
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'unnecessary-backslash'

    msgs = {
        'C8003': (
            "Backslashes are not nice to look at. Please consider avoiding them (use parenthesis etc).",
            'unnecessary-backslash',
            'Emitted when backslash is found at the end of the line, but no necessity of its use.'
            ),
        }

    def visit_module(self, node):
        """
        Unnecessary backslashes.

        :param node:
        :return:
        """
        with open(node.file) as mod_fh:
            for idx, line in enumerate(mod_fh.read().split(os.linesep)):
                line = line.strip()
                if line.endswith("\\") and "with " not in line and not line.startswith("#"):
                    self.add_message("unnecessary-backslash", node=node, line=idx+1)


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(BackslashChecker(linter))
