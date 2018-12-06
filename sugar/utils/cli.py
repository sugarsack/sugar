"""
CLI utils: command line info, coloring, text wrappers etc.
"""

from __future__ import absolute_import, print_function, unicode_literals
import sys


def get_current_component():
    """
    Get currently running component.

    :return:
    """
    return sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ['master', 'client', 'local'] else None
