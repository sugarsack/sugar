# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals
import collections


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
