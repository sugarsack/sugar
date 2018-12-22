"""
Core client operations.
"""

from __future__ import unicode_literals, absolute_import

import os
import errno
import queue

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.transport.serialisable import Serialisable


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
        self.system = SystemEvents(self)
        self.crypto = Crypto()
        self._queue = {"_": queue.Queue()}
        self._proto = {}

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


class SystemEvents(object):
    """
    Happens at system events.
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

    def refresh_keys(self):
        """
        Refresh keys on the disk. If key do not exist, create new.

        :return:
        """
        self.log.info("Refreshing keys")

        for key, key_pem in zip(["private", "public"], self.core.crypto.create_rsa_keypair()):
            key_path = os.path.join(self.pki_path, "{}.pem".format(key))
            self.log.debug("Refreshing {} key as {}".format(key, key_path))
            try:
                os.remove(key_path)
                self.log.debug("Key {} removed".format(key_path))
            except OSError as ex:
                if ex.errno != errno.ENOENT:
                    self.log.error("Error removing {} key: {}".format(key, ex))
            with open(key_path, "wb") as key_fh:
                key_fh.write(key_pem)
                self.log.debug("Key {} written".format(key_path))

        self.log.info("Keys has been re-generated")

    def check_keys(self) -> bool:
        """
        Check if keypair is there and master is registered.
        :return:
        """
        self.log.info("Checking keys in PKI: {}".format(self.core.config.config_path))
        incomplete_keys = 0
        for key in ["public", "private"]:
            if not os.path.exists(os.path.join(self.pki_path, "{}.pem".format(key))):
                self.log.warning("{} key not found".format(key))
                incomplete_keys += 1
        if incomplete_keys:
            self.log.error("Private/public key pair is incomplete or does not exist. Updating.")
            self.refresh_keys()

        return not bool(incomplete_keys)

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
            # self.core.put_message()

        return ret

