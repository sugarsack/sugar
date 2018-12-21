"""
Core client operations.
"""

from __future__ import unicode_literals, absolute_import

import os
import errno

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component


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


class SystemEvents(object):
    """
    Happens at system events.
    """
    def __init__(self, core: ClientCore):
        self.log = get_logger(self)
        self.core = core
        self.pki_path = os.path.join(self.core.config.config_path,
                                     "pki/{}".format(get_current_component()))

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

    def check_keys(self):
        """
        Check if keypair is there and master is registered.
        :return:
        """
        self.log.info("Checking keys in PKI: {}".format(self.core.config.config_path))
        if not os.path.exists(self.pki_path):
            self.log.info("creating directory for keys in: {}".format(self.pki_path))
            os.makedirs(self.pki_path)

        incomplete_keys = 0
        for key in ["public", "private"]:
            if not os.path.exists(os.path.join(self.pki_path, "{}.pem".format(key))):
                self.log.warning("{} key not found".format(key))
                incomplete_keys += 1
        if incomplete_keys:
            self.log.error("Private/public key pair is incomplete or does not exist. Updating.")
            self.refresh_keys()
