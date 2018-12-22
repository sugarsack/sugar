"""
PKI utils
"""

from __future__ import absolute_import, unicode_literals, print_function
import os
import errno

from sugar.lib.logger.manager import get_logger
from sugar.lib.pki import Crypto
from sugar.utils.cli import get_current_component

log = get_logger(__name__)


PUBLIC_KEY_FILENAME = "public_{}.pem".format(get_current_component())
PRIVATE_KEY_FILENAME = "private_{}.pem".format(get_current_component())


def refresh_keys(pki_path: str) -> None:
    """
    Refresh keys on the disk. If key do not exist, create new.

    :return:
    """
    log.info("Refreshing keys")

    for key, key_pem in zip([PRIVATE_KEY_FILENAME, PUBLIC_KEY_FILENAME], Crypto().create_rsa_keypair()):
        key_path = os.path.join(pki_path, key)
        log.debug("Refreshing {} key as {}".format(key, key_path))
        try:
            os.remove(key_path)
            log.debug("Key {} removed".format(key_path))
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                log.error("Error removing {} key: {}".format(key, ex))
        with open(key_path, "wb") as key_fh:
            key_fh.write(key_pem)
            log.debug("Key {} written".format(key_path))

    log.info("Keys has been re-generated")


def check_keys(pki_path: str) -> bool:
    """
    Check if keypair is there and master is registered.
    :return:
    """
    log.info("Checking keys in PKI: {}".format(pki_path))
    incomplete_keys = 0
    for key in [PUBLIC_KEY_FILENAME, PRIVATE_KEY_FILENAME]:
        if not os.path.exists(os.path.join(pki_path, key)):
            log.warning("{} key not found".format(key))
            incomplete_keys += 1
    if incomplete_keys:
        log.error("Private/public key pair is incomplete or does not exist. Updating.")
        refresh_keys(pki_path)

    return not bool(incomplete_keys)
