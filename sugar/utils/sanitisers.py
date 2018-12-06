# coding=utf-8
"""
Input and data sanitisers
"""

from __future__ import absolute_import, print_function, unicode_literals
import re


def join_path(*elements):
    '''
    Join path, cleaning-up all the elements

    :param elements:
    :return:
    '''
    c = re.compile(r'[^A-Za-z0-9]')
    out = ['']
    for el in elements:
        out.append(c.sub('', el))

    return '/'.join(out)
