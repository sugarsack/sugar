# -*- coding: utf-8 -*-
"""
Extra log observers for Twisted.
"""
import logging

from twisted.python import log
from twisted.python import util


class LevelFileLogObserver(log.FileLogObserver):
    """
    Log messages observer. Has internal logging level threshold. Adds log level
    to output messages. See 'twisted.python.log.FileLogObserver' for details.
    """
    def __init__(self, f, level=logging.INFO):
        log.FileLogObserver.__init__(self, f)
        self.log_level = level

    def __call__(self, eventDict):
        self.emit(eventDict)

    def emit(self, eventDict):
        """
        Extends method of the base class by providing support for log level.
        """
        if eventDict['isError']:
            level = logging.ERROR
        elif 'level' in eventDict:
            level = eventDict['level']
        else:
            level = logging.INFO
        if level < self.log_level:
            return

        text = log.textFromEventDict(eventDict)
        if text is None:
            return

        time_str = self.formatTime(eventDict['time'])
        fmt_dict = {
            'level': logging.getLevelName(level),
            'system': eventDict['system'],
            'text': text.replace("\n", "\n\t")
        }
        msg_str = log._safeFormat(
            "%(level)8s:[%(system)s]: %(text)s\n", fmt_dict)

        util.untilConcludes(self.write, "{0} {1}".format(time_str, msg_str))
        util.untilConcludes(self.flush)
