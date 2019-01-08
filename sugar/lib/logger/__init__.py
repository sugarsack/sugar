"""
Logger library for Twisted.
"""

from __future__ import absolute_import, print_function, unicode_literals
import logging

from twisted.python import log
from sugar.lib import exceptions


class Logger(object):
    """
    Turns log levels into `twisted.python.log.msg` corresponding method alias.
    Result is before:

      log.msg(message, level=logging.INFO, system='hello')

    After:

      log.info(message)

    """
    LOG_LEVELS = {
        'all': logging.NOTSET,         # 0
        'debug': logging.DEBUG,        # 10
        'error': logging.ERROR,        # 40
        'critical': logging.CRITICAL,  # 50  <--+
        'info': logging.INFO,          # 20     |
        'warning': logging.WARNING,    # 30     |
        'fatal': logging.FATAL         # 50  <--+
    }

    def __init__(self, name, threshold):
        self.name = name
        self.threshold = threshold
        for method in self.LOG_LEVELS:
            def make_log_level_caller(level):
                """
                Wrap Twisted's log into levels

                :param level: Log level
                :return: Whatever log.msg returns
                """
                def _msg(message, *args, **kwargs):
                    try:
                        if args:
                            message = message.format(*args)
                        elif kwargs:
                            message = message.format(**kwargs)
                    except Exception as err:
                        raise exceptions.SugarRuntimeException(
                            "Formatting log message '{}' failed: {}".format(message, str(err)))
                    if level >= self.threshold:
                        log.msg(message, level=level, system=self.name)

                return _msg

            setattr(self, method, make_log_level_caller(self.LOG_LEVELS[method]))
