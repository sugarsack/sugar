"""
Core Server operations.
"""

from __future__ import unicode_literals, absolute_import

import json
import os
import random
import re
import typing
from multiprocessing import Queue

from twisted.internet import threads, reactor

import sugar.lib.exceptions
import sugar.lib.pki.utils
import sugar.transport
import sugar.utils.files
import sugar.utils.network
import sugar.utils.stringutils

from sugar.components.server.pdatastore import PDataContainer
from sugar.components.server.registry import RuntimeRegistry
from sugar.config import get_config
from sugar.lib.compiler.objresolv import ObjectResolver
from sugar.lib.jobstore import JobStorage
from sugar.lib.jobstore.const import JobTypes
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
from sugar.transport import Serialisable, ServerMsgFactory, ObjectGate
from sugar.utils.cli import get_current_component
from sugar.utils.objects import Singleton
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

    def fire_job_event(self, event: Serialisable, target: PDataContainer,
                       src: str = None, src_path: str = None) -> None:
        """
        Fire an event (usually a remote task).

        :param event: An event to broadcast
        :param target: Selected target
        :param src: Source of the state, if any. Default None
        :param src_path: Path of the source, if source is not None.
        :return: None
        """
        msg = None
        if src or src_path:
            if src is None:
                msg = "No source found for the given path '{}'".format(src_path)
                self.log.error(msg)
            if src_path is None:
                msg = "No path found for the source at '{}' URI".format(event.uri)
                self.log.error(msg)

        if msg is not None:
            raise sugar.lib.exceptions.SugarServerException(msg)

        task_message = ServerMsgFactory().create(jid=event.jid)  # TODO: Better message type to avoid internal segment
        task_message.ret.message = "pig"
        task_message.internal = {
            "function": event.uri,
            "arguments": event.arg,
            "type": None,
            "env": event.env
        }
        if event.kind == sugar.transport.ConsoleMsgFactory.TASK_REQUEST:
            task_message.internal["type"] = JobTypes.RUNNER
            _type = "Runner"
        elif event.kind == sugar.transport.ConsoleMsgFactory.STATE_REQUEST:
            assert src is not None, "State source was not found"
            task_message.internal["type"] = JobTypes.STATE
            task_message.internal["stage"] = "init"  # TODO: First "init", others are "followup"
            task_message.internal["src"] = src
            task_message.internal["src_path"] = src_path
            task_message.internal["uri"] = event.uri
            _type = "State"
        else:
            _type = "Unknown"
        self.log.debug("{} event '{}({})' to host '{}' ({})",
                       _type, event.uri, event.arg, target.host, target.id)
        # Fire
        if task_message.internal["type"] is not None:
            proto = self.get_client_protocol(target.id)  # None due to the network issues (unregister fired)
            if proto is None and self.__retry_calls.get(target.id) != 0:
                self.__retry_calls.setdefault(target.id, 3)
                self.__retry_calls[target.id] -= 1
                pause = random.randint(3, 15)
                self.log.debug("Peer temporarily unavailable for peer {} to fire job {}. Waiting {} seconds.",
                               target.id, event.jid, pause)
                reactor.callLater(pause, self.fire_job_event, event, target, src, src_path)
            else:
                if target.id in self.__retry_calls:
                    del self.__retry_calls[target.id]
                if proto is not None:
                    proto.sendMessage(ServerMsgFactory.pack(task_message), isBinary=True)
                    self.jobstore.set_as_fired(jid=event.jid, target=target)
                    self.log.debug("{} job '{}' has been fired successfully", _type, event.jid)
                else:
                    self.log.debug("{} job '{}' temporarily cannot be fired to the client {}.",
                                   _type, event.jid, target.id)

    def _get_state_source(self, event: Serialisable) -> typing.Tuple:
        """
        Get state source by URI from the environment.
        Returns state source if event kind is the "state request".
        If the event kind is "state request" and source is not found,
        source remains None and "failed" turns into a tuple of two
        elemtns: string template for the error message and arguments
        for its formatting.

        Source will remain None if state kind is not "state request".

        Return format:
          source, relative-to-environment-path, failed

          The "failed" has either empty tuple if no failed, or "msg"
          and args list to "msg" template.

        :param event: Event
        :return: Source string
        """
        failed = ()
        src = None
        if event.kind == sugar.transport.ConsoleMsgFactory.STATE_REQUEST:
            try:
                src_path = ObjectResolver(path=self.config.states.environments(event.env)).resolve(uri=event.uri)
                if os.path.exists(src_path):
                    with sugar.utils.files.fopen(src_path) as src_fh:
                        src = src_fh.read()
            except Exception as exc:
                failed = "No state source available for URI '{}'. {}", [event.uri, str(exc)]

        return src, failed

    def _get_targets(self, event) -> typing.Tuple[list, list]:
        """
        Get targets.

        :return: tuple of online/offline targets.
        """
        return (self.peer_registry.get_targets(query=event.target),
                self.peer_registry.get_offline_targets() if event.offline else [])

    def on_broadcast_state(self, evt, proto) -> None:
        """
        Send state metadata to clients.

        :param evt: an event
        :param proto: peer protocol
        :return: None
        """
        src, failed = self._get_state_source(evt)
        self.log.debug("accepted a state event from the console:\n\tURI: {}\n\tenv: {}\n\tquery: {}\n\targs: {}",
                       evt.uri, evt.env, evt.target, evt.arg)

        msg = sugar.transport.ServerMsgFactory.create_console_msg()
        if not failed:
            clientlist, offline_clientlist = self._get_targets(event=evt)
            if clientlist or offline_clientlist:
                evt.jid = self.jobstore.new(query=evt.target, clientslist=clientlist + offline_clientlist,
                                            uri=evt.uri, args=json.dumps(evt.arg), job_type=JobTypes.STATE,
                                            env=evt.env, kind=evt.kind)
                for target in clientlist:
                    threads.deferToThread(self.fire_job_event, event=evt, target=target, src=src)

            msg.ret.msg_template, msg.ret.msg_args = "State JID: {}", [evt.jid]
        else:
            msg.ret.msg_template, msg.ret.msg_args = failed
        proto.sendMessage(ServerMsgFactory.pack(msg), isBinary=True)

    def on_broadcast_tasks(self, evt, proto) -> None:
        """
        Send task to clients.

        :param evt: an event
        :param proto: peer protocol
        :return: None
        """
        self.log.debug("accepted a runner event from the console:\n\tfunction: {}\n\tquery: {}\n\targs: {}",
                       evt.uri, evt.target, evt.arg)
        clientlist, offline_clientlist = self._get_targets(event=evt)

        msg = sugar.transport.ServerMsgFactory.create_console_msg()
        if clientlist or offline_clientlist:
            evt.jid = self.jobstore.new(query=evt.target, clientslist=clientlist + offline_clientlist,
                                        uri=evt.uri, args=json.dumps(evt.arg), env=evt.env,
                                        job_type=JobTypes.RUNNER, kind=evt.kind)
            for target in clientlist:
                threads.deferToThread(self.fire_job_event, event=evt, target=target)
            self.log.debug("Created a new job: '{}' for {} online and {} offline machines",
                           evt.jid, len(clientlist), len(offline_clientlist))
            msg.ret.msg_template = "Targeted {} machines. JID: {}"
            msg.ret.msg_args = [len(clientlist + offline_clientlist), evt.jid]
        else:
            self.log.error("No targets found for function '{}' on query '{}'.", evt.uri, evt.target)
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
                event.uri = job.uri
                event.env = job.env
                event.arg = json.loads(job.args)
                event.kind = job.kind
                src, failed = self._get_state_source(event)

                if not failed:
                    threads.deferToThread(self.fire_job_event, event=event, target=target, src=src)
                else:
                    msg, args = failed
                    self.log.error(msg, *args)

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
        if evt.kind == sugar.transport.ConsoleMsgFactory.TASK_REQUEST:
            threads.deferToThread(self.on_broadcast_tasks, evt, proto)
        elif evt.kind == sugar.transport.ConsoleMsgFactory.STATE_REQUEST:
            threads.deferToThread(self.on_broadcast_state, evt, proto)

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
            self.log.info("creating directory for keys in '{}'.".format(self.pki_path))
            os.makedirs(self.pki_path)

    def init_state_directories(self) -> None:
        """
        Create state directories according to the configuration.

        :return: None
        """
        for env_name in self.core.config.states.environments:
            path = self.core.config.states.environments(env_name)
            if not os.path.exists(path):
                self.log.info("creating state environment for '{}' in '{}'.", env_name, path)
                try:
                    os.makedirs(path)
                except IOError as exc:
                    self.log.error("Unable to create state environment for '{}' in '{}'.", env_name, path)
                    self.log.critical(str(exc))
                    raise Exception("Aborted due to {}".format(exc))

    def validate_state_aliases(self) -> None:
        """
        Validate state aliases on startup. An alias cannot be a path or URI,
        should contain only letters, hyphens and underscores.

        :return: None
        """
        chk_reg = re.compile(r"\w|[-]")
        for alias in self.core.config.states.aliases or []:
            if chk_reg.sub("", alias):
                self.log.error("Invalid alias: '{}'.", alias)
                raise Exception("Incorrect alias configuration.")

    def on_startup(self):
        """
        This starts on Master startup to reset its initial state.

        :return: None
        """
        self.init_state_directories()
        self.validate_state_aliases()

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
