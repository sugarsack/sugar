"""
Testing peewee
"""

from __future__ import absolute_import, unicode_literals, print_function

import os
import time

from sugar.lib.pki import Crypto
from sugar.lib import six
from sugar.utils.cli import get_current_component
import sugar.utils.files
import sugar.utils.stringutils
import sugar.lib.exceptions

from pony import orm


class KeyStore(object):
    """
    Key Store implementation with the SQLite3.
    """
    db = orm.Database()

    STATUS_CANDIDATE = "candidate"
    STATUS_ACCEPTED = "accepted"
    STATUS_DENIED = "denied"
    STATUS_REJECTED = "rejected"

    LOCKFILE = ".keystore.lck"
    DBFILE = "keystore.db"

    def __init__(self, path):
        """
        Constructor.

        :param dbpath:
        """
        self.__component = get_current_component()

        if self.__component != 'local':
            self.__root_path = os.path.join(path, self.__component)
            self.__keys_path = sugar.utils.files.mk_dirs(os.path.join(self.__root_path, 'keys'))
        self.__lock_file_path = os.path.join(self.__root_path, self.LOCKFILE)
        self.__is_locked = False

        db_name = os.path.join(self.__root_path, self.DBFILE)
        db_mapping = not os.path.exists(db_name)
        self.db.bind(provider="sqlite", filename=db_name, create_db=True)
        if db_mapping:
            self.db.generate_mapping(create_tables=True)

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

        with sugar.utils.files.fopen(self.__lock_file_path, 'wb') as fh_lck:
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

    def get_candidates(self):
        """
        List candidate keys in the store by name.

        :return:
        """
        return orm.select(k for k in StoredKey if k.status == self.STATUS_CANDIDATE)

    def get_accepted(self):
        """
        List accepted keys in the store by name.

        :return:
        """
        return orm.select(k for k in StoredKey if k.status == self.STATUS_ACCEPTED)

    def get_rejected(self):
        """
        List rejected keys in the store by name.

        :return:
        """
        return orm.select(k for k in StoredKey if k.status == self.STATUS_REJECTED)

    def get_denied(self):
        """
        List denied keys in the store by name.

        :return:
        """
        return orm.select(k for k in StoredKey if k.status == self.STATUS_DENIED)

    @orm.db_session
    def add(self, pubkey_pem, hostname, machine_id):
        """
        Add PEM key to the store.

        :param pubkey_pem:
        :return:
        """
        self._lock_transation()
        key = StoredKey(hostname=hostname, fingerprint=Crypto.get_finterprint(pubkey_pem),
                        machine_id=machine_id, filename="{}.bin".format(os.path.join(self.__keys_path, machine_id)),
                        status=self.STATUS_CANDIDATE)

        print('HOSTNAME:', key.hostname)
        print('MACHINE ID:', key.machine_id)

        orm.commit()
        self._unlock_transaction()

    @orm.db_session
    def delete(self, fingerprint):
        """
        Delete PEM key from the store.

        :param pubkey_pem:
        :return:
        """
        self._lock_transation()
        key = self.__get_key_for_status(fingerprint)
        if key is not None:
            orm.delete(k for k in StoredKey if k.fingerprint == fingerprint)
            # delete key from the fs too
        self._unlock_transaction()

    def __get_key_for_status(self, hostname=None, fingerprint=None):
        """
        Get key for the status update.

        :param hostname:
        :param fingerprint:
        :return:
        """
        if hostname is not None:
            key = self.get_key_by_hostname(hostname)
        elif fingerprint is not None:
            key = self.get_key_by_fingerprint(fingerprint)
        else:
            raise sugar.lib.exceptions.SugarKeyStoreException("Hostname or fingerprint needs to be specified")
        return key

    @orm.db_session
    def reject(self, hostname=None, fingerprint=None):
        """
        Reject key by either hostname or fingerprint.
        If both are None, an exception is raised.

        :param hostname:
        :param fingerprint:
        :return:
        """
        self._lock_transation()
        key = self.__get_key_for_status(hostname=hostname, fingerprint=fingerprint)
        if key is not None:
            key.status = self.STATUS_REJECTED
            orm.commit()
        self._unlock_transaction()

    @orm.db_session
    def deny(self, fingerprint):
        """
        Deny key by fingerprint.

        :param fingerprint:
        :return:
        """
        self._lock_transation()
        key = self.__get_key_for_status(fingerprint=fingerprint)
        if key is not None:
            key.status = self.STATUS_DENIED
            orm.commit()
        self._unlock_transaction()

    @orm.db_session
    def accept(self, fingerprint):
        """
        Accept key by fingerprint.

        :param fingerprint:
        :return:
        """
        self._lock_transation()
        key = self.__get_key_for_status(fingerprint=fingerprint)
        if key is not None:
            key.status = self.STATUS_ACCEPTED
            orm.commit()
        self._unlock_transaction()

    def get_key_by_fingerprint(self, fingerprint):
        """
        Get key by fingerprint.

        :param fingerprint:
        :return:
        """
        return orm.select(k for k in StoredKey if k.fingerprint == fingerprint)

    def get_key_by_machine_id(self, machine_id):
        """
        Get key by name.

        :param name:
        :return: Usability status (boolean), key
        """
        return orm.select(k for k in StoredKey if k.machine_id == machine_id)

    def get_key_by_hostname(self, hostname):
        """
        Get key by hostname.

        :param hostname:
        :return:
        """
        return orm.select(k for k in StoredKey if k.hostname == hostname)


class StoredKey(KeyStore.db.Entity):
    """
    Key meta.
    """
    id = orm.PrimaryKey(int, auto=True)
    hostname = orm.Required(str, unique=True)
    machine_id = orm.Required(str, unique=True)
    fingerprint = orm.Required(str, unique=True)
    status = orm.Required(str)
    filename = orm.Required(str, unique=True)
    notes = orm.Optional(str)


if __name__ == '__main__':
    ks = KeyStore("/tmp/ks")
    c = Crypto()
    pri, pub = c.create_rsa_keypair()
    ks.add(pub, "bla", "blabla")
