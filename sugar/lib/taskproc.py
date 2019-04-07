# coding: utf-8
"""
Task processing daemon.
"""
import time
from twisted.internet import reactor, threads
from twisted.internet import task as twisted_task
import twisted.internet.error

from sugar.lib.compat import yaml
from sugar.lib.logger.manager import get_logger
from sugar.lib.compiler.objtask import FunctionObject
from sugar.lib.perq import QueueFactory
from sugar.lib.perq.qexc import QueueEmpty
from sugar.transport import ClientMsgFactory, ObjectGate
import sugar.utils.timeutils


class TaskProcessor:
    """
    Concurrent task processor.
    """
    XLOG_PATH = "/var/cache/sugar/client/tasks"
    XRET_PATH = "/var/cache/sugar/client/responses"

    def __init__(self, loader):
        self.t_counter = 0
        self.log = get_logger(self)
        self.loader = loader
        self._queue = QueueFactory.fs_queue(self.XLOG_PATH).use_notify()
        self._ret_queue = QueueFactory.fs_queue(self.XRET_PATH).use_notify()
        self._d_stop = False
        self._task_looper_marker = True

    def on_task(self, task: FunctionObject) -> (str, dict):
        """
        Process task.

        :param task: FunctionObject
        :raises NotImplementedError: if state is called
        :return dict: result data
        """
        # Todo: probably not FunctionObject, but StateTask *and* FunctionObject.
        self.log.debug("Running task: {}. JID: {}", task, task.jid)

        # TODO: Send message back informing for accepting the task
        uri = "{}.{}".format(task.module, task.function)
        task_source = {
            "command": {
                uri: []
            }
        }
        if task.args:
            task_source["command"][uri].append(task.args)
        if task.kwargs:
            task_source["command"][uri].append(task.kwargs)

        self._add_response(task.jid, src=yaml.dump(task_source))

        try:
            uri = "{module}.{function}".format(module=task.module, function=task.function)
            if task.type == FunctionObject.TYPE_RUNNER:
                result = self.loader.runners[uri](*task.args, **task.kwargs)
                self._add_response(task.jid, finished=True)
            else:
                raise NotImplementedError("State running is not implemented yet")
        except Exception as exc:
            self.log.error("Error running task '{}.{}': {}", task.module, task.function, str(exc))
            result = {}

        return task.jid, result

    def _add_response(self, jid, **kwargs) -> None:
        """
        Add report xlog to the response queue for sending that back to the master.

        :param kwargs: data container for the arbitrary response.
        :return: None
        """
        task_update_info_msg = ClientMsgFactory.create(jid=jid, kind=ClientMsgFactory.KIND_NFO_RESP)
        task_update_info_msg.internal.update(kwargs)
        self._ret_queue.put_nowait(ObjectGate(task_update_info_msg).pack(binary=True))
        self.log.debug("Task has been reported to return Queue")

    def on_task_result(self, result: tuple) -> None:
        """
        Store task results to the returner facility.

        :param result: Resulting data from the performed task, which is a tuple of "(jid, result)".
        :return: None
        """
        jid, data = result
        self.log.debug("Task return: {}, jid: {}", data, jid)
        self._add_response(jid, answer=data.to_json() if data is not None else {},
                           finished=sugar.utils.timeutils.to_iso(),
                           log="not yet implemented")

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

    def next_task(self) -> None:
        """
        Cycle the next task.

        :return: None
        """
        task = None
        while task is None:
            try:
                task = self._queue.get(force=self._task_looper_marker)  # If any old lock still there
                self._task_looper_marker = False
            except QueueEmpty:
                self.log.debug("Skipping concurrent notification: task already taken")
                time.sleep(1)

        self.log.info("Processing task")
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

    def schedule_task(self, task) -> None:
        """
        Schedule task.

        :param task: Task to schedule
        :return: None
        """
        self._queue.put(task)

    def get_response(self, force):
        """
        Get response.
        :return:
        """
        return self._ret_queue.get_nowait(force=force)

    def run(self) -> None:
        """
        Run task processor.

        :return: None
        """
        self.log.info("Task processor start")
        twisted_task.LoopingCall(self.next_task).start(0.1)
        reactor.run()
        self.log.info("Processor stopped")
