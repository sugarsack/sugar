"""
Core Server operations.
"""

from __future__ import unicode_literals, absolute_import

import os
import json
import random
from multiprocessing import Queue
from twisted.internet import threads, reactor

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport import Serialisable, ServerMsgFactory, ObjectGate
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
from sugar.components.server.registry import RuntimeRegistry
from sugar.components.server.pdatastore import PDataContainer
from sugar.lib.jobstore import JobStorage

import sugar.transport
import sugar.lib.pki.utils
import sugar.utils.stringutils
import sugar.utils.network

from sugar.utils.tokens import MasterLocalToken


@Singleton
class ServerCore:
    """
    Server core composite class.
    """

    def __init__(self):
        self.log = get_logger(self)
        self.config = get_config()
        self.cli_db = RegisteredClients()
        self.crypto = Crypto()
        self.system = ServerSystemEvents(self)
        self.keymanager = KeyManagerEvents(self)
        self.keystore = KeyStore(os.path.abspath(self.config.config_path))
        self.master_local_token = MasterLocalToken()
        self.peer_registry = RuntimeRegistry()
        self.peer_registry.keystore = self.keystore
        self.jobstore = JobStorage(get_config())
        self.__retry_calls = {}

    def verify_local_token(self, token):
        """
        Verify local token if local client is authorised to connect.

        :param token: string token
        :return: bool
        """
        return token == self.master_local_token.get_token()

    def fire_event(self, event, target) -> None:
        """
        Fire an event (usually a remote task).

        :param event: An event to broadcast
        :param target: Selected target
        :return: None
        """
        self.log.debug("Sending event '{}({})' to host '{}' ({})", event.fun, event.arg, target.host, target.id)

        task_message = ServerMsgFactory().create(jid=event.jid)
        task_message.ret.message = "ping"
        task_message.internal = {
            "function": event.fun,
            "arguments": event.arg,
        }
        proto = self.get_client_protocol(target.id)  # This might be None due to the network issues (unregister fired)
        if proto is None and self.__retry_calls.get(target.id) != 0:
            self.__retry_calls.setdefault(target.id, 3)
            self.__retry_calls[target.id] -= 1
            pause = random.randint(3, 15)
            self.log.debug("Peer temporarily unavailable for peer {} to fire job {}. Waiting {} seconds.",
                           target.id, event.jid, pause)
            reactor.callLater(pause, self.fire_event, event, target)
        else:
            if target.id in self.__retry_calls:
                del self.__retry_calls[target.id]
            if proto is not None:
                proto.sendMessage(ServerMsgFactory.pack(task_message), isBinary=True)
                self.jobstore.set_as_fired(jid=event.jid, target=target)
                self.log.debug("Job '{}' has been fired successfully", event.jid)
            else:
                self.log.debug("Job '{}' temporarily cannot be fired to the client {}.", event.jid, target.id)

    def on_broadcast_tasks(self, evt, proto) -> None:
        """
        Send task to clients.

        :param evt: an event
        :param proto: peer protocol
        :return: None
        """
        self.log.debug("accepted an event from the local console:\n\tfunction: {}\n\tquery: {}\n\targs: {}",
                       evt.fun, evt.tgt, evt.arg)
        clientlist = self.peer_registry.get_targets(query=evt.tgt)
        offline_clientlist = self.peer_registry.get_offline_targets() if evt.offline else []

        msg = sugar.transport.ServerMsgFactory.create_console_msg()
        if clientlist or offline_clientlist:
            evt.jid = self.jobstore.new(query=evt.tgt, clientslist=clientlist + offline_clientlist,
                                        uri=evt.fun, args=json.dumps(evt.arg),
                                        job_type="runner")
            for target in clientlist:
                threads.deferToThread(self.fire_event, event=evt, target=target)
            self.log.debug("Created a new job: '{}' for {} online and {} offline machines",
                           evt.jid, len(clientlist), len(offline_clientlist))
            msg.ret.msg_template = "Targeted {} machines. JID: {}"
            msg.ret.msg_args = [len(clientlist + offline_clientlist), evt.jid]
        else:
            self.log.error("No targets found for function '{}' on query '{}'.", evt.fun, evt.tgt)
            msg.ret.message = "No targets found"
        proto.sendMessage(ServerMsgFactory.pack(msg), isBinary=True)

    def fire_pending_jobs(self, mid: str) -> None:
        """
        Check pending jobs for the particular machine.

        :param mid: machine ID
        :return: None
        """
        self.log.debug("Checking for pending jobs on {}", mid)
        target = PDataContainer(id=mid, host="")  # TODO: get a proper target with the hostname
        if self.get_client_protocol(mid) is not None:
            for job in self.jobstore.get_scheduled(target):
                event = type("event", (), {})
                event.jid = job.jid
                event.fun = job.uri
                event.arg = json.loads(job.args)
                threads.deferToThread(self.fire_event, event=event, target=target)

    def refresh_client_pdata(self, machine_id: str, traits=None) -> None:
        """
        Register machine connection.

        :param machine_id: string form of the machine ID
        :param traits: traits from the client machine
        :return: None
        """
        assert traits is not None, "No traits has been sent, but they required to be updated on client connect."

        # WARNING: Removal of the peer from the data store is only on key invalidation!
        #          Traits data and P-Data of the peer is always updated on each connect.
        container = PDataContainer(id=machine_id, host=self.peer_registry.get_hostname(machine_id))
        container.traits = traits
        container.pdata = {}  # TODO: Get pdata from the pdata subsystem here
        self.peer_registry.pdata_store.add(container=container)
        self.log.debug("Traits loaded from host '{}' ({})", container.host, container.id)

    def remove_client_protocol(self, proto, tstamp: float) -> None:
        """
        Unregister machine connection.

        :param proto: current protocol instance
        :param tstamp: timestamp
        :return: None
        """
        # STOP: Do not ever remove peer here from the data store!

        self.peer_registry.unregister(proto.get_machine_id(), tstamp)

    def get_client_protocol(self, machine_id: str):
        """
        Get registered client protocol to send a message to the client.

        :param machine_id: string form of the machine ID
        :return: registered client protocol instance
        """
        peer = self.peer_registry.peers.get(machine_id)
        return peer.peer if peer is not None else None

    def console_request(self, evt, proto):
        """
        Accepts request from the console.

        :param evt: an event
        :param proto: protocol of the connected console peer
        :return: immediate response
        """
        if evt.kind == sugar.transport.ServerMsgFactory.TASK_RESPONSE:
            threads.deferToThread(self.on_broadcast_tasks, evt, proto)

    def client_request(self, evt):
        """
        Accepts request from the client.

        :param evt: an event
        :return: Put an event to the queue
        """
        threads.deferToThread(self.cli_db.accept, evt)


class KeyManagerEvents(object):
    """
    KeyManager events.
    """
    def __init__(self, core: ServerCore):
        """
        Constructor

        :param core: ServerCore instance
        """
        self.core = core

    def on_key_status(self, key):
        """
        Action on key status.

        :param key: Serialisable (key)
        :return: None
        """
        self.core.log.info("Key Manager key update")
        client_proto = self.core.get_client_protocol(key.machine_id)
        if client_proto is not None:
            reply = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)
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

        :return: None
        """
        if not sugar.lib.pki.utils.check_keys(self.pki_path):
            # TODO: Clients also should update this.
            # - Send an event?
            # - Client should always ask for pubkey?
            self.log.warning("RSA keys has been updated")

    def on_pub_rsa_request(self) -> Serialisable:
        """
        Return public RSA key.

        :return: Serialisable
        """
        msg = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_PKEY_RESP)
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

        :param msg: Serialisable
        :return: Serialisable
        """
        with open(os.path.join(self.pki_path, self.KEY_PRIVATE)) as priv_mst_kh:
            priv_master_key = priv_mst_kh.read()

        cipher = msg.internal["cipher"]
        signature = msg.internal["signature"]
        machine_id = self.core.crypto.decrypt_rsa(priv_master_key, cipher)

        client_key = None
        for key in self.core.keystore.get_key_by_machine_id(machine_id):
            client_key = key
            if client_key.status in [KeyStore.STATUS_DENIED, KeyStore.STATUS_REJECTED]:
                pem = None
            else:
                pem = self.core.keystore.get_key_pem(client_key)
            if pem is None or not self.core.crypto.verify_signature(pem, cipher, signature):
                self.log.error("SECURITY ALERT: Key signature verification failure. Might be spoofing attack!")
                client_key.status = KeyStore.STATUS_INVALID
            else:
                self.log.info("Signature verification passed.")
                self.core.jobstore.add_host(fqdn=key.hostname, osid=key.machine_id,
                                            ipv4=sugar.utils.network.get_ipv4(key.hostname),
                                            ipv6=sugar.utils.network.get_ipv6(key.hostname))
                self.core.fire_pending_jobs(key.machine_id)
            # TODO: Check for duplicate machine id? This should never happen though
            break

        if not client_key:
            # No key in the database yet. Request for RSA send, then repeat handshake
            self.log.error("RSA key not found for {} or client is not registered yet.".format(machine_id))
            reply = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP)
        elif client_key.status != KeyStore.STATUS_ACCEPTED:
            reply = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)
            reply.internal["payload"] = client_key.status
        else:
            assert client_key.status == KeyStore.STATUS_ACCEPTED
            reply = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_TKEN_RESP)
            reply.internal["payload"] = client_key.status

        return reply

    def on_add_new_rsa_key(self, msg: Serialisable) -> Serialisable:
        """
        Add RSA key to the keystore.

        :param msg: Serialisable
        :return: Serialisable
        """
        reply = ServerMsgFactory().create(kind=ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP)

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
        Put an event message to the queue

        :param evt: an event for the queue
        :return: None
        """
        self._queue.put_nowait(evt)


def get_server_core() -> ServerCore:
    """
    Get server core instance.

    :return: ServerCore instance
    """
    return ServerCore()
