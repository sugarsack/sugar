"""
Sugar Traits
"""
from __future__ import absolute_import, unicode_literals

import copy
from sugar.utils.objects import Singleton


@Singleton
class Traits(object):
    """
    Traits class
    """
    def __init__(self):
        self._data = {}  # Traits container

    @property
    def data(self):
        """
        Returns copy of traits data.
        :return:
        """
        return copy.deepcopy(self._data)
