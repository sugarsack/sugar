# coding: utf-8
"""
Logger extensions for Twisted.
"""
import sys
import logging

from twisted.python import log, util
from twisted.python.logfile import LogFile

from sugar.utils.objects import Singleton
from sugar.lib import six
from sugar.lib.logger import Logger
from sugar.config import get_config


class SugarLogObserver(log.FileLogObserver):
    """
    Logging messages observer.
    """
    def __init__(self, fh, level=logging.INFO):
        log.FileLogObserver.__init__(self, fh)
        self.log_level = level

    def __call__(self, event_data):
        self.emit(event_data)

    def _get_log_level(self, event_data):
        """
        Get proper logging level

        :param level: any log level
        :return: supported log level with default to the current log level
        """
        level = logging.ERROR if bool(event_data.get('isError')) else event_data.get('level', self.log_level)
        return self.log_level if level < self.log_level else level

    def emit(self, event_data):
        """
        Log message emitter

        :param event_data: event data to be emitted
        :return: None
        """
        msg = log.textFromEventDict(event_data)
        if msg:
            if six.PY3:
                if isinstance(msg, six.binary_type):
                    msg = msg.decode("utf-8")
            else:
                if isinstance(msg, six.text_type):
                    msg = msg.encode("utf-8")

            msg = "{tm} {lvl}:[{ssm}]: {txt}\n".format(tm=self.formatTime(event_data['time']),
                                                       lvl=logging.getLevelName(self._get_log_level(event_data)),
                                                       ssm=event_data['system'], txt=msg)
            util.untilConcludes(self.write, msg)
            util.untilConcludes(self.flush)


@Singleton
class LoggerManager(object):
    """
    Logger manager.
    """

    # TODO: get all that from the config (and the whole below)
    def __init__(self):
        self.config = get_config()
        self.logger_store = {}

        for log_cfg in self.config.log:
            path = log_cfg.file if log_cfg.file not in ['STDOUT', 'STDERR'] else None
            out = LogFile.fromFullPath(path, rotateLength=(log_cfg.max_size_mb or 10) * 0x400 * 0x400,
                                       maxRotatedFiles=log_cfg.rotate) if path else getattr(sys, log_cfg.file.lower())
            log.addObserver(SugarLogObserver(out, Logger.LOG_LEVELS[log_cfg.level]))

    def get_logger(self, name):
        """
        Get logger with the specified name.

        :param name: name of the logger
        :return: logger
        """
        if not isinstance(name, six.string_types):
            name = "{}.{}".format(name.__class__.__module__, name.__class__.__name__)

        return self.logger_store.setdefault(name, Logger(name=name,
                                                         threshold=Logger.LOG_LEVELS[self.config.log[0].level]))


get_logger = LoggerManager().get_logger  # pylint: disable=C0103
