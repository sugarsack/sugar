# coding=utf-8
"""
Input and data sanitisers
"""

from __future__ import absolute_import, print_function, unicode_literals
import re
import os


def join_path(*elements, relative=False):
    """
    Join path safely, cleaning-up all the elements

    :param elements:
    :return: path string
    """
    char = re.compile(r'[^A-Za-z0-9]')
    out = ['']
    for elm in elements:
        for part in elm.lstrip(os.path.sep).split(os.path.sep):
            out.append(char.sub('', part))

    out = os.path.sep.join(out)
    return out.lstrip(os.path.sep) if relative else out
