"""
Core client operations.
"""
import os

from twisted.internet import reactor
from twisted.internet import task as twisted_task
import twisted.internet.error

import sugar.lib.pki.utils
import sugar.utils.stringutils
import sugar.utils.network
import sugar.utils.process
import sugar.lib.exceptions

from sugar.config import get_config
from sugar.lib.compat import queue
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
from sugar.lib.exceptions import SugarClientException
from sugar.lib.traits import Traits
from sugar.lib.taskproc import TaskProcessor
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport.serialisable import Serialisable
from sugar.transport import ClientMsgFactory, ServerMsgFactory
from sugar.lib.loader import SugarModuleLoader


# pylint: disable=R0801

class RuntimeStatus:
    """
    Runtime status.
    """
    def __init__(self):
        self.startup = None
        self.reset()

    def reset(self) -> None:
        """
        Reset

        :return: None
        """
        self.startup = True


class HandshakeStatus:
    """
    Handshake status.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.__ended = self.__successful = self.__tries = self.rsa_accept_wait = None
        self.reset()

    def reset(self):
        """
        Reset the handshake status to the initial.

        :return: None
        """
        self.__ended = False
        self.__successful = False
        self.__tries = 0
        self.rsa_accept_wait = False

    @property
    def ended(self):
        """
        Flag: Is handshake ended.

        :return: bool
        """
        return self.__ended

    @property
    def success(self):
        """
        Flag: is handshake succeeded.

        :return: bool
        """
        return self.__successful

    def set_successfull(self):
        """
        Set handshake succeeded.

        :return: None
        """
        self.__successful = True
        self.__ended = True

    def set_failed(self):
        """
        Set handshake failed.

        :return: None
        """
        self.__successful = False
        self.__ended = True

    def start(self):
        """
        Kick handshake status, every time it is restarting its cycle.
        This prevents infinite loop on failure.

        :return: None
        """
        self.__tries += 1
        if self.__tries > 5:
            self.__ended = True
            self.set_failed()


@Singleton
class TaskPool:
    """
    Task pool to collect, run them and get the output back.
    """
    def __init__(self, core):
        self.core = core
        self.processor = TaskProcessor(SugarModuleLoader())
        self.worker = sugar.utils.process.SignalHandlingMultiprocessingProcess(target=self.processor.run)
        self.worker.daemon = True
        self._response_looper_marker = True
        self.log = get_logger(self)

    def start(self) -> None:
        """
        Start internal worker.

        :return: None
        """
        self.worker.start()
        twisted_task.LoopingCall(self.next_response).start(0.02)

    def stop(self) -> None:
        """
        Stop internal worker.

        :return: None
        """
        self.processor.deferred_stop()

        # TODO: wait for actually deferred stop. Now we just killing it.
        if self.worker.is_alive():
            self.worker.kill()

    def add_task(self, task) -> None:
        """
        Schedule task.

        :param task: schedule task to the task processor
        :raises SugarRuntimeException: raised when task worker is not running
        :return: None
        """
        if not self.worker.is_alive():
            raise sugar.lib.exceptions.SugarRuntimeException("Task worker is not running")

        self.processor.schedule_task(task)

    def next_response(self):
        """
        Get a response from the queue.
        :return:
        """
        resp = None
        try:
            resp = self.processor.get_response(self._response_looper_marker)
            self._response_looper_marker = False
        except Exception as exc:
            self.log.error("Error fetching next response: {}", str(exc))
        if resp is not None:
            self.core.broadcast_message(resp)


@Singleton
class ClientCore(object):
    """
    Client.
    """
    def __init__(self):
        """

        """
        self.log = get_logger(self)
        self.config = get_config()
        self.system = ClientSystemEvents(self)
        self.crypto = Crypto()
        self._queue = {"_": queue.Queue()}
        self._proto = {}
        self.traits = Traits()
        self.reactor_connection = None

        self.hds = HandshakeStatus()
        self.rts = RuntimeStatus()

    def set_reactor_connection(self, connection):
        """
        Set pointer to the reactor connection.

        :param connection: Reactor connection
        :return: None
        """
        self.reactor_connection = connection

    def broadcast_message(self, data):
        """
        Send data to all protocols.

        :param data:
        :return:
        """
        for prt_id in self._proto:
            proto = self._proto[prt_id]
            proto.sendMessage(data, is_binary=True)

    def set_protocol(self, proto_id, proto):
        """
        Set protocol.

        :param proto_id: protocol ID
        :param proto: WebsocketProtocol instance
        :return: None
        """
        self._proto.setdefault(proto_id, proto)
        self._queue.setdefault(proto_id, queue.Queue())
        self.log.debug("added protocol with ID {}", proto_id)

    def remove_protocol(self, proto_id):
        """
        Remove protocol.

        :param proto_id: Protocol ID reference
        :return: None
        """
        self.log.debug("removing protocol, ID: {}", proto_id)
        for container in [self._proto, self._queue]:
            try:
                del container[proto_id]
                self.log.all("protocol with the ID {} has been deleted", proto_id)
            except KeyError:
                self.log.error("unable to remove protocol with ID {} from {}", proto_id, container.__class__.__name__)

    def get_queue(self, channel="_") -> queue.Queue:
        """
        Returns message to the master.

        :param channel: queue channel. Global is "_" (default).
        :return: Queue object
        """
        return self._queue[channel]

    def put_message(self, message: Serialisable, channel="_") -> None:
        """
        Places message from the master.

        :param message: message to put into the queue.
        :param channel: queue channel. Global is "_" (default).
        :return: None
        """
        self._queue[channel].put_nowait(message)


class ClientSystemEvents(object):
    """
    Client system events
    """
    MASTER_PUBKEY_FILE = "master_public_key.pem"
    TOKEN_CIPHER_FILE = "master_token.bin"
    SIGNATURE_FILE = "master_signed_token.bin"

    def __init__(self, core: ClientCore):
        self.log = get_logger(self)
        self.core = core
        self.task_pool = TaskPool(self.core)
        self.pki_path = os.path.join(self.core.config.config_path, "pki/{}".format(get_current_component()))
        if not os.path.exists(self.pki_path):
            self.log.info("creating directory for keys in: {}", self.pki_path)
            os.makedirs(self.pki_path)

    def on_startup(self):
        """
        This starts on Client boot.

        :return: None
        """
        sugar.lib.pki.utils.check_keys(self.pki_path)
        self.task_pool.start()

    def on_shutdown(self, *args, **kwargs) -> None:  # pylint: disable=W0613
        """
        Called on Client shutdown (if it is not killed).

        :param args: Common args
        :param kwargs: Common keywords
        :return: None
        """
        for proto in self.core._proto.values():  # pylint: disable=W0212
            try:
                proto.transport.loseConnection()
            except Exception as exc:
                self.log.error("Error shutting down protocol: {}", str(exc))
        self.task_pool.stop()
        try:
            reactor.stop()
        except twisted.internet.error.ReactorNotRunning:
            self.log.debug("Reactor is already stopped by another process.")

    def check_master_pubkey(self) -> bool:
        """
        Check if Master's public key is in place.

        :return: bool
        """
        mpk_path = os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)
        ret = os.path.exists(mpk_path)
        if not ret:
            self.log.warning("master public key '{}' was not found", mpk_path)

        return ret

    def save_master_pubkey(self, pubkey_pem, force=False):
        """
        Save Master's pubkey.

        :param pubkey_pem: public key cipher
        :param force: bool
        :raises SugarClientException: if master public key already exists.
        :return: None
        """
        mpk_path = os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)
        if not os.path.exists(mpk_path) or force:
            with open(mpk_path, "wb") as mpk_h:
                mpk_h.write(sugar.utils.stringutils.to_bytes(pubkey_pem))
            self.log.info("master RSA key has been saved")
        else:
            msg = "master public key already exists: {}".format(mpk_path)
            self.log.error(msg)
            raise SugarClientException(msg)

    def check_master_token(self) -> bool:
        """
        Master token is encrypted by Master's public key this client's machine_id.
        This assumes that the master's pubkey is in place.

        :return: bool
        """
        self.log.debug("verifying master token...")
        tkn_path = os.path.join(self.pki_path, self.TOKEN_CIPHER_FILE)
        ret = os.path.exists(tkn_path)
        if not ret:
            self.log.warning("{} file was not found", tkn_path)
            # self.core.put_message()
        else:
            self.log.debug("master token has been verified")

        return ret

    def create_master_token(self) -> str:
        """
        Create token for the master: encrypted machine_id cipher with the Master's RSA public key.
        It assumes RSA public key is on its place available.

        :raises Exception: if RSA key failed to encrypt the token.
        :return: bytes
        """
        client_id = self.core.traits.data["machine-id"]
        try:
            with open(os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)) as master_pubkey_fh:
                pubkey_rsa = master_pubkey_fh.read()
        except Exception as ex:
            self.log.error("error encrypting token with RSA key: {}", ex)
            raise ex

        return sugar.utils.stringutils.to_bytes(self.core.crypto.encrypt_rsa(pubkey_rsa, client_id))

    def check_master_signature(self):
        """
        Signature of encrypted by master's pubkey should be there.
        This assumes that the master's pubkey is in place.

        :return: bool
        """
        self.log.debug("verifying signature of the token to the master")
        sig_path = os.path.join(self.pki_path, self.SIGNATURE_FILE)
        ret = os.path.exists(sig_path)
        if not ret:
            self.log.warning("signature {} was not found.", sig_path)

        return ret

    def create_master_signature(self, cipher: str) -> str:
        """
        Sign token for the master with the client's key.

        :param cipher: data to sign
        :return: bytes
        """
        with open(os.path.join(self.pki_path, sugar.lib.pki.utils.PRIVATE_KEY_FILENAME), "r") as pkey_h:
            pkey_pem = pkey_h.read()

        return sugar.utils.stringutils.to_bytes(self.core.crypto.sign(priv_key=pkey_pem, data=cipher))

    def wait_rsa_acceptance(self, proto):
        """
        Puts client to wait for the RSA acceptance.

        :param proto: Protocol instance
        :return: None
        """
        self.log.info("waiting for RSA key acceptance...")
        reply = self.core.get_queue().get()
        self.log.debug("RSA key was {}", reply.internal)
        self.core.hds.rsa_accept_wait = False
        proto.restart_handshake()

    def handshake(self, proto):
        """
        Handshake at each client protocol init.

        :param proto: SugarClientProtocol
        :return: None
        """
        key_status = None
        self.log.info("verifying master public key")

        # Phase 1: Get Master's RSA public key on board
        if not self.check_master_pubkey():
            self.log.error("ERROR: Master public key not found")
            proto.sendMessage(ClientMsgFactory.pack(ClientMsgFactory().create(
                kind=ClientMsgFactory.KIND_HANDSHAKE_PKEY_REQ)), is_binary=True)
            reply = self.core.get_queue().get()  # This is blocking and is waiting for the master to continue
            if reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_RESP:
                self.save_master_pubkey(reply.internal["payload"])
        else:
            self.log.debug("master's RSA public key is saved")

        # Phase 2: Tell Master client is authentic
        cipher = self.create_master_token()
        signature = self.create_master_signature(cipher)
        msg = ClientMsgFactory().create(kind=ClientMsgFactory.KIND_HANDSHAKE_TKEN_REQ)
        msg.internal["cipher"] = cipher
        msg.internal["signature"] = signature
        proto.sendMessage(ClientMsgFactory.pack(msg), is_binary=True)

        self.log.debug("master token cipher created, signed and sent")
        reply = self.core.get_queue().get()
        self.log.debug("got server response: {}".format(hex(reply.kind)))

        if reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP:
            self.log.debug("key needs to be sent for the registration")
            registration_request = ClientMsgFactory().create(kind=ClientMsgFactory.KIND_HANDSHAKE_PKEY_REG_REQ)
            registration_request.internal["payload"] = sugar.lib.pki.utils.get_public_key(self.pki_path)
            registration_request.internal["machine-id"] = self.core.traits.data.get('machine-id')
            registration_request.internal["host-fqdn"] = self.core.traits.data.get("host-fqdn")
            proto.sendMessage(ClientMsgFactory.pack(registration_request), is_binary=True)
            self.log.debug("RSA key bound to the metadata and sent")
        elif reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP:
            if reply.internal.get("payload") == KeyStore.STATUS_CANDIDATE:
                self.log.debug("the key needs to be accepted")
                self.core.hds.rsa_accept_wait = True
            elif reply.internal.get("payload") != KeyStore.STATUS_ACCEPTED:
                self.core.hds.set_failed()
                key_status = reply.internal["payload"]
                self.log.info("RSA key is {}".format(key_status))
        elif reply.kind == ServerMsgFactory.KIND_HANDSHAKE_TKEN_RESP:
            self.log.debug("master token response: {}".format(reply.internal["payload"]))
            key_status = reply.internal["payload"]
            if key_status == KeyStore.STATUS_ACCEPTED:
                self.core.hds.set_successfull()
                proto.on_authenticated_start()
            else:
                self.core.hds.set_failed()
            self.log.info("RSA key has been {}".format(key_status))

        if key_status is not None and key_status != KeyStore.STATUS_ACCEPTED:
            proto.factory.reactor.stop()
        else:
            proto.restart_handshake()
