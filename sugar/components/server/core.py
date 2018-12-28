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
from sugar.transport import Serialisable, ServerMsgFactory, ObjectGate
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
import sugar.transport
import sugar.lib.pki.utils
import sugar.utils.stringutils
from sugar.utils.tokens import MasterLocalToken


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
        self.keymanager = KeyManagerEvents(self)
        self.keystore = KeyStore(os.path.abspath(self.config.config_path))
        self.master_local_token = MasterLocalToken()
        self.__client_connection_protocols = {}  # Machine-ID to Client protocols mapping

    def verify_local_token(self, token):
        """
        Verify local token if local client is authorised to connect.

        :param token:
        :return:
        """
        return token == self.master_local_token.get_token()

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

    def register_client_protocol(self, machine_id, proto):
        """
        Register machine connection.

        :param machine_id:
        :param proto:
        :return:
        """
        if getattr(proto, "machine_id", None):
            self.__client_connection_protocols.setdefault(machine_id,  proto)
            self.log.info("Registered client connection with the machine id: {}".format(machine_id))

    def remove_client_protocol(self, proto):
        """
        Unregister machine connection.

        :param proto:
        :return:
        """
        machine_id = proto.get_machine_id()
        if machine_id in self.__client_connection_protocols:
            del self.__client_connection_protocols[machine_id]
            self.log.info("Removed client connection with the machine id: {}".format(machine_id))

    def get_client_protocol(self, machine_id):
        """
        Get registered client protocol to send a message to the client.

        :param machine_id:
        :return:
        """
        return self.__client_connection_protocols.get(machine_id)

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


class KeyManagerEvents(object):
    """
    KeyManager events.
    """
    def __init__(self, core: ServerCore):
        """
        Constructor
        :param core:
        """
        self.core = core

    def on_key_status(self, key):
        """
        Action on key status.
        :param key:
        :return:
        """
        self.core.log.info("Key Manager key update")
        print(">>>", key.hostname)
        print(">>>", key.fingerprint)
        print(">>>", key.machine_id)
        print(">>>", key.status)
        print("---")
        client_proto = self.core.get_client_protocol(key.machine_id)
        if client_proto is not None:
            reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)
            reply.internal["payload"] = key.status
            client_proto.sendMessage(ObjectGate(reply).pack(True), True)
            if key.status != KeyStore.STATUS_ACCEPTED:
                client_proto.dropConnection()


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

        client_key = None
        for key in self.core.keystore.get_key_by_machine_id(machine_id):
            client_key = key
            pem = self.core.keystore.get_key_pem(client_key)
            if not self.core.crypto.verify_signature(pem, cipher, signature):
                self.log.error("SECURITY ALERT: Key signature verification failure. Might be spoofing attack!")
                client_key.status = KeyStore.STATUS_INVALID
            else:
                self.log.info("Signature verification passed.")
            # TODO: Check for duplicate machine id? This should never happen though
            break

        if not client_key:
            # No key in the database yet. Request for RSA send, then repeat handshake
            self.log.info("RSA key not found for {} or client is not registered yet.".format(machine_id))
            reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP)
        elif client_key.status != KeyStore.STATUS_ACCEPTED:
            reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)
            reply.internal["payload"] = client_key.status
        else:
            assert client_key.status == KeyStore.STATUS_ACCEPTED
            reply = ServerMsgFactory().create(ServerMsgFactory.KIND_HANDSHAKE_TKEN_RESP)
            reply.internal["payload"] = client_key.status

        return reply

    def on_add_new_rsa_key(self, msg: Serialisable) -> Serialisable:
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
