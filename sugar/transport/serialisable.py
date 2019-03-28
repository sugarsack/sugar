"""
General objects for the serialisation.
"""
from __future__ import absolute_import, unicode_literals

import json
import datetime
import collections
import pickle


class ObjectGate(object):
    """
    Gate to serialise/pack serialisable objects.
    """
    OBJ_CNT = '.'  # Object container marker

    def __init__(self, obj=None):
        self.__obj = obj
        self.__data = {}

    def _loader(self, ref, obj=None):
        """
        Load data.

        :param ref: JSON
        :param obj: Object reference. Default: None.
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

    def load(self, obj, binary=False):
        """
        Load serialisable object.

        :param obj: Binary
        :param binary: bool
        :raises Exception: if ObjectGate failed
        :return: Serialisable
        """
        if binary:
            obj = pickle.loads(obj)

        if not isinstance(obj, collections.Mapping):
            raise Exception("Object Gate exception")
        self.__obj = self._loader(obj)
        return self.__obj

    def _dumper(self, ref, data=None):
        """
        Dump data recursively.

        :param ref: reference object
        :param data: data to dump. Default: None
        :return: Serialisable
        """
        if data is None:
            data = {self.OBJ_CNT: None}

        for attr_name, attr in ref.__dict__.items():
            if isinstance(attr, Serialisable):
                data[attr_name] = {self.OBJ_CNT: None}
                self._dumper(attr, data[attr_name])
            data.setdefault(attr_name, attr)

        return data

    def pack(self, binary=False):
        """
        Pack serialisable object.

        :param binary: bool
        :return: binary or JSON
        """
        data = self._dumper(self.__obj)
        return pickle.dumps(data) if binary else data

    def _json(self, ref, data=None):
        """
        Dump data recursively.

        :param ref: reference object
        :param data: data to dump. Default: None
        :return: Serialisable
        """
        if data is None:
            data = {}

        for attr_name, attr in ref.__dict__.items():
            if isinstance(attr, (list, tuple)):
                content = []
                for obj in attr:
                    content.append(self._json(obj))
                attr = content
            if isinstance(attr, Serialisable):
                data[attr_name] = {}
                self._json(attr, data[attr_name])
            if isinstance(attr, datetime.datetime):
                attr = attr.isoformat()

            # Filter unknown away
            if isinstance(attr, (dict, list, tuple, str,
                                 int, float, bool, type(None))):
                data.setdefault(attr_name, attr)

        return data

    def to_json(self) -> str:
        """
        To JSON.

        :return: json string
        """
        return json.dumps(self._json(self.__obj))

    def to_dict(self) -> str:
        """
        To dictionary, that later will be dumped to JSON.

        :return:
        """
        return self._json(self.__obj)


# pylint: disable=R0902
class Serialisable:
    """
    Serialisable container.
    """
    def __init__(self):
        """
        Constructor.
        """

    def __getattr__(self, item):
        return self.__dict__.setdefault(item, Serialisable())
# pylint: enable=R0902
