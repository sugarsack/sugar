"""
Core Server operations.
"""

from __future__ import unicode_literals, absolute_import

import os

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from multiprocessing import Queue
from twisted.internet import threads
import sugar.transport
import sugar.lib.pki.utils


@Singleton
class ServerCore(object):
    """
    Server
    """
    def __init__(self):
        """

        """
        self.log = get_logger(self)
        self.config = get_config()
        self.cli_db = RegisteredClients()
        self.system = ServerSystemEvents(self)

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


class ServerSystemEvents(object):
    """
    Server system events.
    """
    KEY_PUBLIC = "public.pem"
    KEY_PRIVATE = "private.pem"

    def __init__(self, core: ServerCore):
        self.log = get_logger(self)
        self.core = core
        self.pki_path = os.path.join(self.core.config.config_path,
                                     "pki/{}".format(get_current_component()))
        if not os.path.exists(self.pki_path):
            self.log.info("creating directory for keys in: {}".format(self.pki_path))
            os.makedirs(self.pki_path)

    def on_startup(self):
        """
        This starts on Master startup to reset its initial state.

        :return:
        """
        if not sugar.lib.pki.utils.check_keys(self.pki_path):
            # TODO: Clients also should update this.
            # - Send an event?
            # - Client should always ask for pubkey?
            self.log.warning("RSA keys has been updated")


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


def get_server_core():
    return ServerCore()
