# coding: utf-8

"""
Object utils
"""
import re
import typing

from sugar.lib import six


class Singleton(object):
    """
    Decorator to turn any class into a singleton.

    :param object:
    :return:
    """

    def __init__(self, cls):
        self.__class_ref__ = cls
        self.__ref__ = None

    def __call__(self, *args, **kwargs):
        if self.__ref__ is None:
            self.__ref__ = self.__class_ref__(*args, **kwargs)
        return self.__ref__


def str_to_type(val: str) -> typing.Any:
    """
    Determine type of the value from the string expression.

    :param val: string value to be parsed from
    :return: a type object
    """
    val = six.text_type(val)
    if ',' in val:
        _val = []
        for inner in val.split(","):
            _val.append(str_to_type(inner))
        val = _val[::]
        del _val
    elif val.lower() in ['true', 'false']:
        val = val.lower() == 'true'
    elif re.search(r"\d+", val):
        try:
            val = int(val, 16 if val.lower().startswith('0x') else 10)
        except (ValueError, TypeError):
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = six.text_type(val)
    else:
        val = six.text_type(val)

    return val
