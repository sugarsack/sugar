# coding=utf-8
"""
Input and data sanitisers
"""

from __future__ import absolute_import, print_function, unicode_literals
import re


def join_path(*elements):
    """
    Join path, cleaning-up all the elements

    :param elements:
    :return: path string
    """
    char = re.compile(r'[^A-Za-z0-9]')
    out = ['']
    for elm in elements:
        out.append(char.sub('', elm))

    return '/'.join(out)
