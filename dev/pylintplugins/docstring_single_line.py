"""
Each docstring should not be a single-line.
"""

import os

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class DocstringNewlineChecker(checkers.BaseChecker):
    """
    PEP8 (1) allows single line. However, to keep a standard,
    text should always start from the new line.

    1. https://www.python.org/dev/peps/pep-0008/#documentation-strings
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'docstring-newlines'

    msgs = {
        'C8001': (
            "Docstring definition error: %s",
            'docstring-newlines',
            'Emitted when docstring is not multi-line.'
            ),
        }

    def _check_docstring(self, node):
        """
        Check if docstring always starts and ends from/by triple double-quotes
        and they are on the new line.

        :param node:
        :return:
        """
        if hasattr(node, "doc") and node.doc:
            doc = node.doc.strip("\t").strip(" ")
            msg = None
            if not doc.startswith(os.linesep):
                msg = "should start with the newline after triple double-quotes"
            if not doc.endswith(os.linesep):
                msg = "should end with the newline before triple double-quotes"
            if msg is not None:
                self.add_message("docstring-newlines", node=node, args=(msg,))

    @utils.check_messages('docstring-triple-quotes')
    def visit_functiondef(self, node):
        """
        Examine function or method.

        :param node:
        :return:
        """
        self._check_docstring(node)

    def visit_classdef(self, node):
        """
        Examine class definition.

        :param node:
        :return:
        """
        self._check_docstring(node)

    def visit_module(self, node):
        """
        Examine module.

        :param node:
        :return:
        """
        self._check_docstring(node)


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(DocstringNewlineChecker(linter))
