# coding: utf-8
"""
Task processing daemon.
"""
import time
from twisted.internet import reactor, threads

from sugar.lib.logger.manager import get_logger
from sugar.lib.compiler.objtask import FunctionObject
from sugar.lib.perq import QueueFactory
from sugar.lib.perq.qexc import QueueEmpty


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

    def on_task(self, task: FunctionObject):
        """
        Process task.

        :param :
        :return:
        """
        self.log.debug("Running task: {}", task)
        try:
            uri = "{module}.{function}".format(module=task.module, function=task.function)
            result = self.loader.runners[uri](*task.args, **task.kwargs)
        except Exception as exc:
            self.log.error("Error running task '{}.{}': {}", task.module, task.function, str(exc))
            result = {}

        return result

    def on_task_result(self, data):
        """
        Return task results.

        :param data:
        :return:
        """
        self.log.debug("Task return: {}", data)
        # TODO: Pass resulting data to the receiver (store)

        # Decrease tasks counter
        if self.t_counter:
            self.t_counter -= 1

        # [Re]fire deferred stop.
        # This will occur only if deferred_stop() has been once fired
        # from the outside. Otherwise this process will keep running.
        if self._d_stop:
            self.deferred_stop()

    def deferred_stop(self):
        """
        Fire worker's deferred stop, which will stop
        this process only after all tasks are finished.

        :param args:
        :param kwargs:
        :return:
        """
        if not self._d_stop:
            self._d_stop = True

        if not self.t_counter:
            self.log.info("Task processor shut down")
            reactor.stop()

    def retask(self, first=False):
        task = None
        while task is None:
            try:
                task = self._queue.get(force=first)  # If any old lock still there
            except QueueEmpty as exc:
                self.log.debug("Skipping concurrent notification: task already taken")
                time.sleep(1)

        threads.deferToThread(self.on_task, task).addCallback(self.on_task_result)
        self.t_counter += 1

        while True:
            try:
                task = self._queue.get_nowait()
                d = threads.deferToThread(self.on_task, task).addCallback(self.on_task_result)
                self.t_counter += 1
            except QueueEmpty:
                self.log.debug("No more tasks")
                break

        threads.deferToThread(lambda: self.retask())

    def schedule_task(self, task):
        """
        Schedule task.

        :param task:
        :return:
        """
        self._queue.put(task)

    def run(self):
        """
        Run task processor.

        :return:
        """
        self.log.info("Task processor start")
        self.retask(first=True)
        reactor.run()
        self.log.info("Processor stopped")
