# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals
import collections


class ImmutableDict(dict):
    """
    Immutable dictionary.
    """
    class AttributeAccessError(Exception):
        """
        Raise an access error
        """

    def __getitem__(self, key):
        item = super(ImmutableDict, self).__getitem__(key)
        if isinstance(item, dict):
            item = ImmutableDict(item)
        return item

    def __set__(self, instance, value):
        raise ImmutableDict.AttributeAccessError('Access to a protected value')

    def __setattr__(self, key, value):
        raise ImmutableDict.AttributeAccessError('Access to a protected attribute')

    def __delitem__(self, key):
        raise ImmutableDict.AttributeAccessError('Attempt to delete protected key')

    def __delattr__(self, item):
        raise ImmutableDict.AttributeAccessError('Attempt to delete protected item')

    def __setitem__(self, key, value):
        raise ImmutableDict.AttributeAccessError('Access to a protected attribute')

    def update(self, other=None, **kwargs):
        """
        Protect from updating content.

        :param other:
        :param kwargs:
        :return:
        """
        raise ImmutableDict.AttributeAccessError('Attempt to update protected dictionary')

    def setdefault(self, key, value=None):
        """
        Protect from setting the default value.

        :param key:
        :param value:
        :return:
        """
        raise ImmutableDict.AttributeAccessError('Attempt to set default value to a protected dictionary')


class ObjectMap(object):
    '''
    Object map access. KeyError is missing as the default is to None.
    '''
    def __getattr__(self, item):
        return self.__dict__.get(item)


def dict_to_object(src):
    '''
    Creates object out of dictionary.

    :param src:
    :return:
    '''
    obj = ObjectMap()
    for key in src:
        if isinstance(src[key], collections.Mapping):
            setattr(obj, key, dict_to_object(src[key]))
        else:
            setattr(obj, key, src[key])

    return obj


def merge_dicts(dst, src):
    '''

    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    '''

    for key in src:
        if (key in dst and isinstance(dst[key], dict)
                and isinstance(src[key], collections.Mapping)):
            merge_dicts(dst[key], src[key])
        else:
            dst[key] = src[key]
