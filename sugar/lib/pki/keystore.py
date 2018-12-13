"""
Keystore and clients db.
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import time
import pickle

from sugar.lib.pki import Crypto
import sugar.utils.files
import sugar.utils.stringutils
import sugar.lib.exceptions
from sugar.lib import six
from sugar.cli import SugarCLI


class StoredKey(object):
    """
    Machine public key with the metadata.
    It is assigned to the specific unique ID of the machine.
    """
    STATUS_CANDIDATE = "candidate"
    STATUS_ACCEPTED = "accepted"
    STATUS_DENIED = "denied"
    STATUS_REJECTED = "rejected"

    def __init__(self, name, pubkey_pem):
        """
        Key container object.

        :param pubkey_pem: Public key (PEM)
        """
        self.__pem = pubkey_pem
        self.__name = name
        self.__fingerprint = Crypto.get_finterprint(self.__pem)
        self.__status = self.STATUS_CANDIDATE

    @property
    def name(self):
        """
        Return key name (simplified fingerprint).

        :return:
        """
        return self.__name

    @property
    def fingerprint(self):
        """
        Return fingerprint of the machine.
        :return:
        """
        return self.__fingerprint

    def accept(self):
        """
        Accept key.

        :return:
        """
        self.__status = self.STATUS_ACCEPTED

    def reject(self):
        """
        Reject key.

        :return:
        """
        self.__status = self.STATUS_REJECTED

    def deny(self):
        """
        Deny key.

        :return:
        """
        self.__status = self.STATUS_DENIED


class _KeyStoreDB(object):
    """
    KeyStore database class.
    """
    LOCKFILE = ".keystore.lck"

    def __init__(self, path, component=None):
        """
        Keystore main class.

        :param path: Path to the keystore.
        """
        if component is None or component not in SugarCLI.COMPONENTS:
            raise sugar.lib.exceptions.SugarRuntimeException("Unknown component")
        self.__component = component

        if self.__component != 'local':
            self.__root_path = os.path.join(path, component)
            self.__keys_path = sugar.utils.files.mk_dirs(os.path.join(self.__root_path, 'keys'))
            self.__space_path = sugar.utils.files.mk_dirs(os.path.join(self.__root_path, 'space'))
        self.__lock_file_path = os.path.join(self.__root_path, self.LOCKFILE)
        self.__is_locked = False

        # Indexes
        self.__index_fingpt = {}
        self.__index_candidate = {}
        self.__index_accepted = {}
        self.__index_rejected = {}
        self.__index_denied = {}

    def _store_key(self, key):
        """
        Store key in the FS, add to the index.

        :param key:
        :return:
        """

        # with sugar.utils.files.atomic_write()

    def _remove_key(self, key):
        """
        Remove key from the FS, delete from the index.

        :param key:
        :return:
        """

    def _lock_transation(self, timeout=30):
        """
        Lock the FS.
        Timeout 30 seconds by default.
        Should be more than enough even on [N]ot [F]ile [S]ystem.

        :return:
        """
        while timeout > 0:
            if os.path.exists(self.__lock_file_path):
                time.sleep(0.5)
                timeout -= 0.5
            else:
                break

        with sugar.utils.files.fopen(self.__lock_file_path, 'w') as fh_lck:
            fh_lck.write(sugar.utils.stringutils.to_bytes(six.text_type(os.getpid())))
            self.__is_locked = True

        return self.__is_locked

    def _unlock_transaction(self, timeout=30):
        """
        Unlock the FS.
        Timeout 30 seconds by default.

        :return:
        """
        if self.__is_locked:
            try:
                with sugar.utils.files.fopen(self.__lock_file_path, 'r') as fh_lck:
                   lock_pid = int(fh_lck.read().strip())
            except Exception:
                lock_pid = None

            if lock_pid is None:
                sugar.utils.files.remove(self.__lock_file_path)

            if lock_pid is not None and lock_pid != os.getpid() and os.path.exists(self.__lock_file_path):
                while timeout > 0:
                    if os.path.exists(self.__lock_file_path):
                        time.sleep(0.5)
                        timeout -= 0.5
                    else:
                        sugar.utils.files.remove(self.__lock_file_path)
                        self.__is_locked = False

        return not self.__is_locked


class KeyStore(_KeyStoreDB):
    """
    Keystore
    """
    def get_candidates(self):
        """
        List candidate keys in the store by name.

        :return:
        """
        return self.__index_candidate.keys()

    def get_accepted(self):
        """
        List accepted keys in the store by name.

        :return:
        """
        return self.__index_accepted.keys()

    def get_rejected(self):
        """
        List rejected keys in the store by name.

        :return:
        """
        return self.__index_rejected.keys()

    def get_denied(self):
        """
        List denied keys in the store by name.

        :return:
        """
        return self.__index_denied.keys()

    def add(self, pubkey_pem):
        """
        Add PEM key to the store.

        :param pubkey_pem:
        :return:
        """
        key = StoredKey(pubkey_pem)

    def delete(self, pubkey_pem):
        """
        Delete PEM key from the store.

        :param pubkey_pem:
        :return:
        """

    def get_key_by_fingerprint(self, fingerprint):
        """
        Get key by fingerprint.

        :param fingerprint:
        :return:
        """

    def get_key_by_name(self, name):
        """
        Get key by name.

        :param name:
        :return: Usability status (boolean), key
        """

