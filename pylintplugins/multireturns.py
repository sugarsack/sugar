"""
Multiple return statements checker to enforce Dijkstra's SESE.
"""
import astroid

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class MultipleReturnChecker(checkers.BaseChecker):
    """
    Class to collect return statements.

    Generally, multiple return statements are not bad. However it seems leads to write
    quite spaghettish code and thus produced result is not so great to supporting in the long run.
    Therefore multiple return statements is better to be just avoided.

    NOTE: in some cases it might be better to use multiple return statements, thus this
          checker can be considered suppressed.
    """
    __implements__ = interfaces.IAstroidChecker

    name = 'multiple-return-statements'

    msgs = {
        'R8001': (
            "Multiple returns in a function or a method considered harmful (even if you do not think so)",
            'multiple-return-statements',
            'Emitted when a multiple return statements are found in a function or method'
            ),
        }

    def collect_returns(self, node, returns=0):
        """
        Collect return statements.

        :param node:
        :return:
        """
        if isinstance(node, astroid.Return):
            returns += 1
        for method in dir(node):
            obj = getattr(node, method)
            if isinstance(obj, list) and obj:
                for element in obj:
                    returns = self.collect_returns(element, returns=returns)

        return returns

    @utils.check_messages('multiple-return-statements')
    def visit_functiondef(self, node):
        """
        Checks for presence of return statement at the end of a function
        "return" or "return None" are useless because None is the default
        return type if they are missing
        """
        if node.body and self.collect_returns(node) > 1:
            self.add_message("multiple-return-statements", node=node)


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(MultipleReturnChecker(linter))
