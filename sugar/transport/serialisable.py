"""
General objects for the serialisation.
"""
from __future__ import absolute_import, unicode_literals

import collections


class ObjectGate(object):
    """
    Gate to serialise/dump serialisable objects.
    """
    OBJ_CNT = '.'  # Object container marker

    def __init__(self, obj=None):
        self.__obj = obj
        self.__data = {}

    def _loader(self, ref, obj=None):
        """
        Load data.

        :param ref:
        :return:
        """
        if obj is None:
            obj = Serialisable()

        for key, val in ref.items():
            if isinstance(val, collections.Mapping):
                if self.OBJ_CNT in val:
                    setattr(obj, key, Serialisable())
                    self._loader(val, getattr(obj, key))
            obj.__dict__.setdefault(key, val)

        return obj

    def load(self, obj):
        """
        Load serialisable object.

        :param obj:
        :return:
        """
        if not isinstance(obj, collections.Mapping):
            raise Exception("Object Gate exception")
        self.__obj = self._loader(obj)
        return self.__obj

    def _dumper(self, ref, data=None):
        """
        Dump data recursively.

        :param ref:
        :return:
        """
        if data is None:
            data = {self.OBJ_CNT: None}

        for attr_name, attr in ref.__dict__.items():
            if isinstance(attr, Serialisable):
                data[attr_name] = {self.OBJ_CNT: None}
                self._dumper(attr, data[attr_name])
            data.setdefault(attr_name, attr)

        return data

    def dump(self):
        """
        Dump serialisable object.

        :return:
        """
        self.__data = self._dumper(self.__obj)
        return self.__data


class Serialisable(object):
    """
    Serialisable container.
    """
    def __init__(self):
        """
        Constructor.
        """

    def __getattr__(self, item):
        return self.__dict__.setdefault(item, Serialisable())
