"""
Core client operations.
"""

from __future__ import unicode_literals, absolute_import

import os
import queue

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
import sugar.lib.pki.utils
import sugar.utils.stringutils
import sugar.utils.network
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport.serialisable import Serialisable
from sugar.transport import ClientMsgFactory, ServerMsgFactory, ObjectGate
from sugar.lib.exceptions import SugarClientException
from sugar.lib.traits import Traits


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
        for container in [self._proto, self._queue]:
            try:
                del container[id]
                self.log.debug("Removed protocol with ID {} from {}".format(id, container.__class__.__name__))
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
        self.log.info("Verifying master public key")
        mpk_path = os.path.join(self.pki_path, self.MASTER_PUBKEY_FILE)
        ret = os.path.exists(mpk_path)
        if not ret:
            self.log.warning("Master public key '{}' was not found".format(mpk_path))
            # self.core.put_message()

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
        client_id = sugar.utils.network.generate_client_id()
        self.log.info("Creating master token...")

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
        self.log.info("Creating signature of the master token...")

        with open(os.path.join(self.pki_path, sugar.lib.pki.utils.PRIVATE_KEY_FILENAME), "r") as pkey_h:
            pkey_pem = pkey_h.read()

        return sugar.utils.stringutils.to_bytes(self.core.crypto.sign(priv_key=pkey_pem, data=cipher))

