"""
Core client operations.
"""

from __future__ import unicode_literals, absolute_import

import os

from sugar.config import get_config
from sugar.lib.compat import queue
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.lib.pki.keystore import KeyStore
from sugar.lib.exceptions import SugarClientException
from sugar.lib.traits import Traits
import sugar.lib.pki.utils
import sugar.utils.stringutils
import sugar.utils.network
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport.serialisable import Serialisable
from sugar.transport import ClientMsgFactory, ServerMsgFactory


class HandshakeStatus(object):
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

        :return:
        """
        self.__ended = False
        self.__successful = False
        self.__tries = 0
        self.rsa_accept_wait = False

    @property
    def ended(self):
        """
        Flag: Is handshake ended.

        :return:
        """
        return self.__ended

    @property
    def success(self):
        """
        Flag: is handshake succeeded.

        :return:
        """
        return self.__successful

    def set_successfull(self):
        """
        Set handshake succeeded.

        :return:
        """
        self.__successful = True
        self.__ended = True

    def set_failed(self):
        """
        Set handshake failed.

        :return:
        """
        self.__successful = False
        self.__ended = True

    def start(self):
        """
        Kick handshake status, every time it is restarting its cycle.
        This prevents infinite loop on failure.

        :return:
        """
        self.__tries += 1
        if self.__tries > 5:
            self.__ended = True
            self.set_failed()


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
        self.hs = HandshakeStatus()

    def set_reactor_connection(self, connection):
        """
        Set pointer to the reactor connection.

        :param connection:
        :return:
        """
        self.reactor_connection = connection

    def set_protocol(self, id, proto):
        """
        Set protocol.

        :param proto:
        :return:
        """
        self._proto.setdefault(id, proto)
        self._queue.setdefault(id, queue.Queue())
        self.log.debug("Added protocol with ID {}".format(id))

    def remove_protocol(self, id):
        """
        Remove protocol.

        :param id:
        :return:
        """
        self.log.debug("Removing protocol, ID: {}".format(id))
        for container in [self._proto, self._queue]:
            try:
                del container[id]
            except KeyError:
                self.log.error("Unable to remove protol with ID {} from {}".format(id, container.__class__.__name__))

    def get_queue(self, channel="_") -> queue.Queue:
        """
        Returns message to the master.

        :return:
        """
        return self._queue[channel]

    def put_message(self, message: Serialisable, channel="_") -> None:
        """
        Places message from the master.

        :return:
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
        self.pki_path = os.path.join(self.core.config.config_path,
                                     "pki/{}".format(get_current_component()))
        if not os.path.exists(self.pki_path):
            self.log.info("creating directory for keys in: {}".format(self.pki_path))
            os.makedirs(self.pki_path)

    def on_startup(self):
        """
        This starts on Client boot.
        :return:
        """
        sugar.lib.pki.utils.check_keys(self.pki_path)

    def check_master_pubkey(self) -> bool:
        """
        Check if Master's public key is in place.

        :return:
        """
        mpk_path = os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)
        ret = os.path.exists(mpk_path)
        if not ret:
            self.log.warning("Master public key '{}' was not found".format(mpk_path))

        return ret

    def save_master_pubkey(self, pubkey_pem, force=False):
        """
        Save Master's pubkey.

        :param pubkey_pem:
        :return:
        """
        mpk_path = os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)
        if not os.path.exists(mpk_path) or force:
            with open(mpk_path, "wb") as mpk_h:
                mpk_h.write(sugar.utils.stringutils.to_bytes(pubkey_pem))
            self.log.info("Master RSA key has been saved")
        else:
            raise SugarClientException("Master public key already exists: {}".format(mpk_path))

    def check_master_token(self) -> bool:
        """
        Master token is encrypted by Master's public key this client's machine_id.
        This assumes that the master's pubkey is in place.

        :return:
        """
        self.log.info("Verifying master token")
        tkn_path = os.path.join(self.pki_path, self.TOKEN_CIPHER_FILE)
        ret = os.path.exists(tkn_path)
        if not ret:
            self.log.warning("{} file was not found".format(tkn_path))
            # self.core.put_message()

        return ret

    def create_master_token(self) -> str:
        """
        Create token for the master: encrypted machine_id cipher with the Master's RSA public key.
        It assumes RSA public key is on its place available.

        :return:
        """
        client_id = self.core.traits.data["machine-id"]
        try:
            with open(os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)) as master_pubkey_fh:
                pubkey_rsa = master_pubkey_fh.read()
        except Exception as ex:
            self.log.error("Error encrypting token with RSA key: {}".format(ex))
            raise ex

        return sugar.utils.stringutils.to_bytes(self.core.crypto.encrypt_rsa(pubkey_rsa, client_id))

    def check_master_signature(self):
        """
        Signature of encrypted by master's pubkey should be there.
        This assumes that the master's pubkey is in place.

        :return:
        """
        self.log.info("Verifying signature of the token to the master")
        sig_path = os.path.join(self.pki_path, self.SIGNATURE_FILE)
        ret = os.path.exists(sig_path)
        if not ret:
            self.log.warning("Signature {} was not found.".format(sig_path))

        return ret

    def create_master_signature(self, cipher: str) -> str:
        """
        Sign token for the master with the client's key.

        :return:
        """
        with open(os.path.join(self.pki_path, sugar.lib.pki.utils.PRIVATE_KEY_FILENAME), "r") as pkey_h:
            pkey_pem = pkey_h.read()

        return sugar.utils.stringutils.to_bytes(self.core.crypto.sign(priv_key=pkey_pem, data=cipher))

    def wait_rsa_acceptance(self, proto):
        """
        Puts client to wait for the RSA acceptance.

        :param proto:
        :return:
        """
        self.log.info("Waiting for RSA key acceptance...")
        reply = self.core.get_queue().get()
        self.log.info("RSA key was {}".format(reply.internal))
        self.core.hs.rsa_accept_wait = False
        proto.restart_handshake()

    def handshake(self, proto):
        """
        Handshake at each client protocol init.

        :return:
        """
        key_status = None
        self.log.debug("Master/client handshake begin")
        self.log.info("Verifying master public key")

        # Phase 1: Get Master's RSA public key on board
        if not self.check_master_pubkey():
            self.log.error("ERROR: Master public key not found")
            proto.sendMessage(ClientMsgFactory.pack(ClientMsgFactory().create(
                ClientMsgFactory.KIND_HANDSHAKE_PKEY_REQ)), is_binary=True)
            reply = self.core.get_queue().get()  # This is blocking and is waiting for the master to continue
            if reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_RESP:
                self.save_master_pubkey(reply.internal["payload"])
        else:
            self.log.debug("Master's RSA public key is saved")

        # Phase 2: Tell Master client is authentic
        cipher = self.create_master_token()
        signature = self.create_master_signature(cipher)
        msg = ClientMsgFactory().create(ClientMsgFactory.KIND_HANDSHAKE_TKEN_REQ)
        msg.internal["cipher"] = cipher
        msg.internal["signature"] = signature
        proto.sendMessage(ClientMsgFactory.pack(msg), is_binary=True)

        self.log.debug("Master token cipher created, signed and sent")
        reply = self.core.get_queue().get()
        self.log.debug("Got server response: {}".format(hex(reply.kind)))

        if reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP:
            self.log.debug("KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP")
            self.log.info("Key needs to be sent for the registration")
            registration_request = ClientMsgFactory().create(ClientMsgFactory.KIND_HANDSHAKE_PKEY_REG_REQ)
            registration_request.internal["payload"] = sugar.lib.pki.utils.get_public_key(self.pki_path)
            registration_request.internal["machine-id"] = self.core.traits.data.get('machine-id')
            registration_request.internal["host-fqdn"] = self.core.traits.data.get("host-fqdn")
            proto.sendMessage(ClientMsgFactory.pack(registration_request), is_binary=True)
            self.log.debug("RSA key bound to the metadata and sent")
        elif reply.kind == ServerMsgFactory.KIND_HANDSHAKE_PKEY_STATUS_RESP:
            self.log.debug("KIND_HANDSHAKE_PKEY_STATUS_RESP")
            if reply.internal.get("payload") == KeyStore.STATUS_CANDIDATE:
                self.log.debug("Handshake: Waiting for key to be accepted...")
                self.core.hs.rsa_accept_wait = True
            elif reply.internal.get("payload") != KeyStore.STATUS_ACCEPTED:
                self.core.hs.set_failed()
                key_status = reply.internal["payload"]
                self.log.info("RSA key {}".format(key_status))
        elif reply.kind == ServerMsgFactory.KIND_HANDSHAKE_TKEN_RESP:
            self.log.debug("KIND_HANDSHAKE_PKEY_TKEN_RESP")
            self.log.debug("Master token response: {}".format(reply.internal["payload"]))
            key_status = reply.internal["payload"]
            if key_status == KeyStore.STATUS_ACCEPTED:
                self.core.hs.set_successfull()
            else:
                self.core.hs.set_failed()
            self.log.info("RSA key {}".format(key_status))

        if key_status is not None and key_status != KeyStore.STATUS_ACCEPTED:
            proto.factory.reactor.stop()
        else:
            proto.restart_handshake()
