"""
Logger library for Twisted.
"""

from __future__ import absolute_import, print_function, unicode_literals
import logging

from twisted.python import log


class Logger(object):
    """
    Turns log levels into `twisted.python.log.msg` corresponding method alias.
    Result is before:

      log.msg(message, level=logging.INFO, system='hello')

    After:

      log.info(message)

    """
    LOG_LEVELS = {
        'all': logging.NOTSET,
        'debug': logging.DEBUG,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'fatal': logging.FATAL
    }

    def __init__(self, name):
        self.name = name
        for method in self.LOG_LEVELS:
            def make_log_level_caller(level):
                """
                Wrap Twisted's log into levels
                :param level:
                :return:
                """
                def _msg(message):
                    log.msg(message, level=level, system=self.name)
                return _msg

            setattr(self, method, make_log_level_caller(self.LOG_LEVELS[method]))
