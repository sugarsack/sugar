"""
Sugar runtime exceptions
"""
from __future__ import absolute_import, unicode_literals

import time
from sugar.lib import six
import sugar.utils.exitcodes


class SugarException(Exception):
    """
    Base exception class.
    All Sugar exceptions should be subclassed from here.
    """
    __prefix__ = "General error"
    errcode = sugar.utils.exitcodes.EX_GENERIC

    def __init__(self, msg="", errcode=None):
        if not isinstance(msg, six.string_types):
            msg = six.text_type(msg)
        msg = "{}: {}".format(self.__prefix__, msg)
        super(SugarException, self).__init__(msg)
        self.message = self.strerror = msg
        if errcode is not None:
            self.errcode = errcode

    def __unicode__(self):
        return self.strerror

    @staticmethod
    def get_errcode(exc) -> int:
        """
        Get an error code from the exception.

        :param exc: Exception object
        :return: an error code. Default: EX_GENERIC
        """
        return getattr(exc, "errcode", sugar.utils.exitcodes.EX_GENERIC)

    def pack(self):
        """
        Serialise exception for transfer.

        :return: dictionary in format {"message": payload, "args": arguments}
        """
        return {'message': six.text_type(self) if six.PY3 else self.__unicode__(),
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
    def __init__(self, message, time_start=None):
        SugarException.__init__(self, message)
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


# Compiler
class SugarSCException(SugarException):
    """
    General Sugar State Compiler exception.
    """
    __prefix__ = "State Compiler error"


class SugarSCResolverException(SugarException):
    """
    Sugar State Compiler resolver exception.
    """
    __prefix__ = "State Compiler resolver error"


class SugarSCRenderException(SugarException):
    """
    Sugar State Compiler render exception.
    """
    __prefix__ = "State Compiler render error"


# Loader
class SugarLoaderException(SugarException):
    """
    General Sugar module loader exception.
    """
    __prefix__ = "Sugar Loader error"


# Job store
class SugarJobStoreException(SugarException):
    """
    Sugar JobStore general exception.
    """
    __prefix__ = "Sugar JobStore error"


# Module data
class SugarModuleException(SugarException):
    """
    Sugar Module general exception.
    """
    __prefix__ = "Suger Module error"
