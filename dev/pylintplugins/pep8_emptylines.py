"""
PEP8: look for two empty lines between functions, one empty line between methods.
"""

import os

from pylint import checkers
from pylint import interfaces


class PEP8EmptyLinesChecker(checkers.BaseChecker):
    """
    PEP8 asks for:
      - Two empty lines between module functions
      - One empty line between class methods
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'pep8-empty-lines'
    msgs = {
        'E3010': (
            "Expected %s",
            'pep8-empty-lines',
            'Emitted when backslash is found at the end of the line, but no necessity of its use.'
            ),
        }

    def get_empty_lines(self, offset, index):
        """
        Get empty lines from the offset.

        :param offset:
        :param index:
        :return:
        """
        lines = 0
        for char in index[:offset][::-1]:
            if char == "c":
                continue

            if char == "-":
                lines += 1
            elif char == "d":
                lines = None
                break
            else:
                break
        return lines

    def visit_module(self, node):
        """
        Calculate lines.

        :param node:
        :return:
        """
        index = []
        # Gather map of the source
        with open(node.file) as mod_fh:
            for idx, line in enumerate(mod_fh.read().split(os.linesep)):
                if not line:
                    index.append("-")
                elif line.startswith("def "):
                    index.append("f")
                elif not line.startswith("def ") and line.strip().startswith("def "):
                    index.append("m")
                elif ("'''" in line or '"""' in line or line.endswith("'")
                      or line.endswith('"') or line.strip().startswith("#")):
                    index.append("d")
                elif line.strip().startswith("@"):
                    index.append("c")
                else:
                    index.append("#")

        for idx, element in enumerate(index):
            if idx < 2:
                continue
            if element in ["f", "m"]:
                offset = self.get_empty_lines(idx, index)
                if offset is not None:
                    if element == "f" and offset != 2:
                        self.add_message("pep8-empty-lines", node=node, line=idx + 1,
                                         args=("2 blank lines before function, found {}.".format(offset),))
                    elif element == "m" and offset != 1:
                        self.add_message("pep8-empty-lines", node=node, line=idx + 1,
                                         args=("1 blank line before class method, found {}.".format(offset or "nothing"),))


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(PEP8EmptyLinesChecker(linter))
