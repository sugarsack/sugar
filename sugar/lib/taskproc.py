# coding: utf-8
"""
Task processing daemon.
"""

from sugar.lib.perq import QueueFactory
from sugar.lib.logger.manager import get_logger


class TaskProcessor:
    """
    Concurrent task processor.
    """
    XLOG_PATH = "/tmp/task-processor"

    def __init__(self, loader):
        self.t_counter = 0
        self.log = get_logger(self)
        self.loader = loader
        self._queue = QueueFactory.fs_queue(self.XLOG_PATH).use_notify()
        self._d_stop = False
