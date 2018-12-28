"""
Sugar Traits
"""
from __future__ import absolute_import, unicode_literals

import copy
import collections
from sugar.utils.objects import Singleton
import sugar.lib.traits.features


@Singleton
class Traits(object):
    """
    Traits class
    """
    def __init__(self):
        self._data = collections.OrderedDict()
        self.reload()

    def reload(self):
        """
        [re]load traits.

        :return:
        """
        self._data = {}
        for t_obj_n in dir(sugar.lib.traits.features):
            t_obj = getattr(sugar.lib.traits.features, t_obj_n)
            f_provides, f_type = [getattr(t_obj, attr, None) for attr in ("_sugar_provides", "_sugar_type")]
            if f_type == "trait" and f_provides is not None:
                self._data[f_provides] = t_obj()

    @property
    def data(self):
        """
        Returns copy of traits data.
        :return:
        """
        return copy.deepcopy(self._data)
