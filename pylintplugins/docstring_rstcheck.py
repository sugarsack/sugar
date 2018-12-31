"""
Check if docstring is a proper reStructuredText.
"""

import rstcheck

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class DocstringRSTChecker(checkers.BaseChecker):
    """
    Docstrings should be a proper reStructuredText format.
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'docstring-rst-format'

    msgs = {
        'E8001': (
            "Docstring reStructuredText format error: %s",
            'docstring-rst-format',
            'Emitted when docstring has errors in reStructuredText or is not one.'
            ),
        }

    @utils.check_messages('docstring-triple-quotes')
    def visit_functiondef(self, node):
        """
        Check if docstring always starts and ends from/by triple double-quotes
        and they are on the new line.
        """
        if hasattr(node, "doc") and node.doc:
            out = list(rstcheck.check(node.doc.strip()))
            if out:
                messages = []
                for errcode, msg in out:
                    messages.append(msg)
                self.add_message("docstring-rst-format", node=node, args=(", ".join(messages),))


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(DocstringRSTChecker(linter))
