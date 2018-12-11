"""
Sugar runtime exceptions
"""
from __future__ import absolute_import, unicode_literals

from sugar.lib import six


class SugarException(Exception):
    """
    Base exception class.
    All Sugar exceptions should be subclassed from here.
    """
    def __init__(self, msg=""):
        if not isinstance(msg, six.string_types):
            msg = six.text_type(msg)
        super(SugarException, self).__init__(msg)
        self.message = self.strerror = msg

    def __unicode__(self):
        return self.strerror

    def pack(self):
        """
        Serialise exception for transfer.

        :return:
        """
        return {'message':  six.text_type(self) if six.PY3 else self.__unicode__(),
                'args': self.args}


# Runtime
class SugarRuntimeException(SugarException):
    """
    Sugar runtime exception.
    """


# Console
class SugarConsoleException(SugarException):
    """
    General console exception.
    """


# Client
class SugarClientException(SugarException):
    """
    General client exception.
    """


# Server
class SugarServerException(SugarException):
    """
    General server exception.
    """
