"""
Core Server operations.
"""

from __future__ import unicode_literals, absolute_import

import os
from multiprocessing import Queue
from twisted.internet import threads

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport import Serialisable, ServerMsgFactory
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
import sugar.transport
import sugar.lib.pki.utils
import sugar.utils.stringutils
from sugar.utils import MasterLocalToken


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
        self.crypto = Crypto()
        self.system = ServerSystemEvents(self)
        self.keystore = KeyStore(os.path.abspath(self.config.config_path))
        self.master_local_token = MasterLocalToken()

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
    KEY_PUBLIC = "public_master.pem"
    KEY_PRIVATE = "private_master.pem"

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

    def on_pub_rsa_request(self) -> Serialisable:
        """
        Return public RSA key.

        :return:
        """
        msg = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_RESP)
        with open(os.path.join(self.pki_path, self.KEY_PUBLIC)) as rsa_h:
            msg.internal["payload"] = rsa_h.read()

        return msg

    def on_token_request(self, msg: Serialisable) -> Serialisable:
        """
        Return reply on token verification. Key can be:

          - Candidate
          - Rejected
          - Denied
          - Accepted

        :param msg:
        :return:
        """
        with open(os.path.join(self.pki_path, self.KEY_PRIVATE)) as priv_mst_kh:
            priv_master_key = priv_mst_kh.read()

        cipher = msg.internal["cipher"]
        signature = msg.internal["signature"]
        machine_id = self.core.crypto.decrypt_rsa(priv_master_key, cipher)
        res = self.core.keystore.get_key_by_machine_id(machine_id)
        if not res:
            # No key in the database yet. Request for RSA send, then repeat handshake
            self.log.info("RSA key not found for {}. Client is not registered yet.".format(machine_id))
            reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP)
        else:
            # Check if token is accepted or denied/rejected
            raise NotImplementedError("Not implemented yet")
            #reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_TKEN_RESP)
            #reply.internal["payload"] = self.core.keystore.STATUS_CANDIDATE

        return reply

    def on_register_rsa_key(self, msg: Serialisable) -> Serialisable:
        """
        Add RSA key to the keystore.

        :param msg:
        :return:
        """
        reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)

        found = False
        for key in self.core.keystore.get_key_by_machine_id(msg.internal["machine-id"]):
            if key.machine_id == msg.internal["machine-id"]:
                reply.internal["payload"] = key.status
                found = True

        if not found:
            self.core.keystore.add(pubkey_pem=msg.internal["payload"],
                                   hostname=msg.internal["host-fqdn"],
                                   machine_id=msg.internal["machine-id"])
            reply.internal["payload"] = self.core.keystore.STATUS_CANDIDATE

        return reply


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
