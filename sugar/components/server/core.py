"""
Core Server operations.
"""

from __future__ import unicode_literals, absolute_import

from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton
from multiprocessing import Queue
from twisted.internet import threads
import sugar.transport


class RegisteredClients(object):
    """
    Clients database.
    Purpose:
      - Accepts clients registration.
      - Tells online client status
      - Matches clients by query
      - Notifies clients by protocol
    """

    def __init__(self):
        self.all = {}
        self.registered = {}
        self._queue = Queue()

    def accept(self, evt):
        """

        :param evt:
        :return:
        """
        self._queue.put_nowait(evt)


@Singleton
class ServerCore(object):
    """
    Server
    """
    def __init__(self):
        """

        """
        self.log = get_logger(self)
        self.cli_db = RegisteredClients()

    def _send_task_to_clients(self, evt):
        """
        Send task to clients.

        :param evt:
        :return:
        """
        print('-' * 80)
        print("SEND TASK TO CLIENTS")
        print(evt.jid)
        print('-' * 80)

    def console_request(self, evt):
        """
        Accepts request from the console.

        :return: immediate response
        """
        if evt.kind == sugar.transport.ServerMsgFactory.TASK_RESPONSE:
            threads.deferToThread(self._send_task_to_clients, evt)

        msg = sugar.transport.ServerMsgFactory.create_console_msg()
        msg.ret.message = "Task has been accepted"
        return evt

    def client_request(self, evt):
        """
        Accepts request from the client.

        :return:
        """
        threads.deferToThread(self.cli_db.accept, evt)


def get_server_core():
    return ServerCore()
