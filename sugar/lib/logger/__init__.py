# -*- coding: utf-8 -*-
"""
Logger extensions for Twisted.
"""
import logging

from twisted.python import log


class Logger(object):
    """
    Wrapper of 'twisted.python.log.msg' function. Makes easy to set log levels
    and 'system' channel to log messages.
    """
    def __init__(self, name):
        self.name = name

    def critical(self, message):
        """
        Enlog message with CRITICAL level.
        """
        self._enlog(message, logging.CRITICAL)

    def error(self, message):
        """
        Enlog message with ERROR level.
        """
        self._enlog(message, logging.ERROR)

    def warning(self, message):
        """
        Enlog message with WARNING level.
        """
        self._enlog(message, logging.WARNING)

    def info(self, message):
        """
        Enlog message with INFO level.
        """
        self._enlog(message, logging.INFO)

    def debug(self, message):
        """
        Enlog message with DEBUG level.
        """
        self._enlog(message, logging.DEBUG)

    def _enlog(self, message, level):
        """
        Helper method for enlogging message with specisied log level.
        """
        log.msg(message, level=level, system=self.name)


class Manager(object):
    """
    Simplified version of 'logging.Manager'.
    """
    def __init__(self):
        self.loggers = {}

    def getLogger(self, name):
        """
        Get or create new logger with specisied name.
        """
        #if not isinstance(name, str):
        #    raise TypeError("A logger name must be string or Unicode")
        #if isinstance(name, str):
        #    name = name.encode("utf-8")
        logger = self.loggers.get(name)
        if logger is None:
            logger = Logger(name)
            self.loggers[name] = logger
        return logger


getLogger = Manager().getLogger
