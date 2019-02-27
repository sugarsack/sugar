# coding: utf-8
"""
Task processing daemon.
"""
import time
from twisted.internet import reactor, threads
import twisted.internet.error

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

    def on_task(self, task: FunctionObject) -> dict:
        """
        Process task.

        :param task: FunctionObject
        :raises NotImplementedError: if state is called
        :return dict: result data
        """
        # Todo: probably not FunctionObject, but StateTask *and* FunctionObject.
        self.log.debug("Running task: {}", task)
        try:
            uri = "{module}.{function}".format(module=task.module, function=task.function)
            if task.type == FunctionObject.TYPE_RUNNER:
                result = self.loader.runners[uri](*task.args, **task.kwargs)
            else:
                raise NotImplementedError("State running is not implemented yet")
        except Exception as exc:
            self.log.error("Error running task '{}.{}': {}", task.module, task.function, str(exc))
            result = {}

        return result

    def on_task_result(self, data) -> None:
        """
        Store task results to the returner facility.

        :param data: Resulting data from the performed task.
        :return: None
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

    def deferred_stop(self) -> None:
        """
        Fire worker's deferred stop, which will stop
        this process only after all tasks are finished.

        :return: None
        """
        if not self._d_stop:
            self._d_stop = True

        if not self.t_counter:
            self.log.info("Task processor shut down")
            try:
                reactor.stop()
            except twisted.internet.error.ReactorNotRunning:
                self.log.debug("Reactor is no longer running")

    def next_task(self, first=False) -> None:
        """
        Cycle the next task.

        :param first: If this is a first call, any existing lock will be removed.
        :return: None
        """
        task = None
        while task is None:
            try:
                task = self._queue.get(force=first)  # If any old lock still there
            except QueueEmpty:
                self.log.debug("Skipping concurrent notification: task already taken")
                time.sleep(1)

        threads.deferToThread(self.on_task, task).addCallback(self.on_task_result)
        self.t_counter += 1

        while True:
            try:
                task = self._queue.get_nowait()
                threads.deferToThread(self.on_task, task).addCallback(self.on_task_result)
                self.t_counter += 1
            except QueueEmpty:
                self.log.debug("No more tasks")
                break

        threads.deferToThread(lambda: self.next_task())

    def schedule_task(self, task) -> None:
        """
        Schedule task.

        :param task: Task to schedule
        :return: None
        """
        self._queue.put(task)

    def run(self) -> None:
        """
        Run task processor.

        :return: None
        """
        self.log.info("Task processor start")
        self.next_task(first=True)
        reactor.run()
        self.log.info("Processor stopped")
