# coding: utf-8
"""
Structs utility.
"""

from __future__ import absolute_import, print_function, unicode_literals
import collections
import copy


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

        :param other: -
        :param kwargs: -
        :return: -
        """
        raise ImmutableDict.AttributeAccessError('Attempt to update protected dictionary')

    def setdefault(self, key, value=None):
        """
        Protect from setting the default value.

        :param key: -
        :param value: -
        :return: -
        """
        raise ImmutableDict.AttributeAccessError('Attempt to set default value to a protected dictionary')


class ObjectMap(object):
    """
    Object map access. KeyError is missing as the default is to None.
    """
    def __getattr__(self, item):
        return self.__dict__.get(item)

    def __call__(self, *args, **kwargs):
        return self.__getattr__(args[0])

    def __iter__(self):
        for key in self.__dict__:
            yield key


def dict_to_object(src):
    """
    Creates object out of dictionary.

    :param src: dictionary
    :return: object
    """
    obj = ObjectMap()
    for key in src:
        if isinstance(src[key], collections.Mapping):
            setattr(obj, key, dict_to_object(src[key]))
        elif isinstance(src[key], (list, tuple)):
            val = []
            for item in src[key]:
                if isinstance(item, collections.Mapping):
                    item = dict_to_object(item)
                val.append(item)
            setattr(obj, key, val)
        else:
            setattr(obj, key, src[key])

    return obj


def merge_dicts(dst, src):
    """

    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    :param dst: dict onto which the merge is executed
    :param src: dct merged into
    :return: None
    """

    for key in src:
        if (key in dst and isinstance(dst[key], dict)
                and isinstance(src[key], collections.Mapping)):
            merge_dicts(dst[key], src[key])
        else:
            dst[key] = src[key]


def merge_missing(dst, src):
    """
    Merge missing keys from one dict to another.

    :param dst: dict onto which the merge is executed
    :param src: dict merged into
    :return: None
    """
    for key in src:
        if key not in dst:
            dst[key] = src[key]


# pylint: disable=R0911
def update(dest, upd, recursive_update=True, merge_lists=False):
    """
    Recursive version of the default dict.update

    Merges upd recursively into dest

    If recursive_update=False, will use the classic dict.update, or fall back
    on a manual merge (helpful for non-dict types like FunctionWrapper)

    If merge_lists=True, will aggregate list object types instead of replace.
    The list in ``upd`` is added to the list in ``dest``, so the resulting list
    is ``dest[key] + upd[key]``. This behavior is only activated when
    recursive_update=True. By default merge_lists=False.

    When merging lists, duplicate values are removed. Values already
    present in the ``dest`` list are not added from the ``upd`` list.

    :param dest: destination dict
    :param upd: source dict
    :param recursive_update: bool
    :param merge_lists: bool
    :return: None
    """
    if (not isinstance(dest, collections.Mapping)) or (not isinstance(upd, collections.Mapping)):
        raise TypeError('Cannot update using non-dict types in dictupdate.update()')
    updkeys = list(upd.keys())
    if not set(list(dest.keys())) & set(updkeys):
        recursive_update = False
    if recursive_update:
        for key in updkeys:
            val = upd[key]
            try:
                dest_subkey = dest.get(key, None)
            except AttributeError:
                dest_subkey = None
            if isinstance(dest_subkey, collections.Mapping) and isinstance(val, collections.Mapping):
                ret = update(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif isinstance(dest_subkey, list) and isinstance(val, list):
                if merge_lists:
                    merged = copy.deepcopy(dest_subkey)
                    merged.extend([x for x in val if x not in merged])
                    dest[key] = merged
                else:
                    dest[key] = upd[key]
            else:
                dest[key] = upd[key]
        return dest

    try:
        for key in upd:
            dest[key] = upd[key]
    except AttributeError:
        # not a dict
        for key in upd:
            dest[key] = upd[key]

    return dest
# pylint: enable=R0911
