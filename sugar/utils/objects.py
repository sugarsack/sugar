# coding: utf-8

"""
Object utils
"""


class Singleton(object):
    '''
    Decorator to turn any class into a singleton.

    :param object:
    :return:
    '''

    def __init__(self, cls):
        self.__class_ref__ = cls
        self.__ref__ = None

    def __call__(self, *args, **kwargs):
        if self.__ref__ is None:
            self.__ref__ = self.__class_ref__(*args, **kwargs)
        return self.__ref__

