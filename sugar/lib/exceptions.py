"""
Sugar runtime exceptions
"""
from __future__ import absolute_import, unicode_literals

import time
from sugar.lib import six


class SugarException(Exception):
    """
    Base exception class.
    All Sugar exceptions should be subclassed from here.
    """
    __prefix__ = "General error"

    def __init__(self, msg=""):
        if not isinstance(msg, six.string_types):
            msg = six.text_type(msg)
        msg = "{}: {}".format(self.__prefix__, msg)
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
    __prefix__ = "Runtime error"


class SugarDependencyException(SugarException):
    """
    Sugar dependency installation exception:
    something is missing (needs to be specified).
    """
    __prefix__ = "Dependency error"


class SugarFileLockException(SugarException):
    """
    Used when an error occurs obtaining a file lock
    """
    def __init__(self, message, time_start=None, *args, **kwargs):
        SugarException.__init__(self, message, *args, **kwargs)
        if time_start is None:
            self.time_start = time.time()
        else:
            self.time_start = time_start


class SugarKeyStoreException(SugarException):
    """
    Used when keystore exception occurs.
    """
    __prefix__ = "KeyStore error"


class SugarConfigurationException(SugarException):
    """
    Used when configuration exception occurs (wrong or not found).
    """
    __prefix__ = "Configuration error"


# Console
class SugarConsoleException(SugarException):
    """
    General console exception.
    """
    __prefix__ = "Console-specific error"


# Client
class SugarClientException(SugarException):
    """
    General client exception.
    """
    __prefix__ = "Client error"


# Server
class SugarServerException(SugarException):
    """
    General server exception.
    """
    __prefix__ = "Server error"
