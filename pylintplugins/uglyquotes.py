"""
Ugly triple-quotes (on the same line)
"""

import os

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class TripleDoublequotesChecker(checkers.BaseChecker):
    """
    While PEP8 [1] allows triple-quotes on the same line,
    here multiple quotes should stay alone, text should start from the new line.
    Rules apply:

      - Triple quotes should be double-quotes
      - Text should always start from the new line

    *1. https://www.python.org/dev/peps/pep-0008/#documentation-strings
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'docstring-triple-double-quotes'

    msgs = {
        'R8002': (
            "Any docstring should have triple double-quotes and start from the new line.",
            'docstring-triple-double-quotes',
            'Emitted when docstring is not multi-line and has no triple double-quotes.'
            ),
        }

    @utils.check_messages('docstring-triple-quotes')
    def visit_functiondef(self, node):
        """
        Check if docstring always starts and ends from/by triple double-quotes
        and they are on the new line.
        """
        if hasattr(node, "doc") and node.doc:
            if not node.doc.startswith(os.linesep) or node.doc.endswith(os.linesep):
                self.add_message("docstring-triple-double-quotes", node=node)

    def visit_module(self, node):
        """
        Get the entire module source and see if there are triple quotes.
        :param node:
        :return:
        """
        with open(node.file) as mod_fh:
            for idx, line in enumerate(mod_fh.read().split(os.linesep)):
                if "'''" in line:
                    self.add_message("docstring-triple-double-quotes", node=node, line=idx+1)


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(TripleDoublequotesChecker(linter))
