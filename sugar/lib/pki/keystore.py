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
from sugar.transport.serialisable import Serialisable

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
        self.db.bind(provider="sqlite", filename=db_name, create_db=True)
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
                if os.path.getctime(self.__lock_file_path) + timeout < time.time():
                    break
                time.sleep(0.5)
                timeout -= 0.5
            else:
                break

        with sugar.utils.files.fopen(self.__lock_file_path, 'wb') as fh_lck:
            fh_lck.write(sugar.utils.stringutils.to_bytes(six.text_type(os.getpid())))
            self.__is_locked = True

        return self.__is_locked

    def _unlock_transaction(self, timeout=30, force=False):
        """
        Unlock the FS.
        Timeout 30 seconds by default.

        :return:
        """
        try:
            with sugar.utils.files.fopen(self.__lock_file_path, 'r') as fh_lck:
                lock_pid = int(fh_lck.read().strip())
                if os.getpid() == lock_pid:
                    lock_pid = None
        except Exception:
            lock_pid = None

        try:
            if os.path.getctime(self.__lock_file_path) + timeout < time.time() or force:
                lock_pid = None
        except Exception:
            lock_pid = None

        if lock_pid is None:
            sugar.utils.files.remove(self.__lock_file_path)
        elif lock_pid != os.getpid() and os.path.exists(self.__lock_file_path):
            while timeout > 0:
                if os.path.exists(self.__lock_file_path):
                    time.sleep(0.5)
                    timeout -= 0.5
                else:
                    sugar.utils.files.remove(self.__lock_file_path)
                    self.__is_locked = False

        return not self.__is_locked

    @orm.db_session
    def __commit(self):
        force = False
        try:
            orm.commit()
        except orm.core.TransactionIntegrityError as ex:
            force = True
            raise sugar.lib.exceptions.SugarKeyStoreException(ex)
        finally:
            self._unlock_transaction(force=force)

    @orm.db_session
    def __get_keys_by_status(self, status):
        """
        Get keys by status.

        :param status:
        :return:
        """
        ret = []
        for obj in orm.select(k for k in StoredKey if k.status == status):
            ret.append(obj.clone())

        return ret

    def get_candidates(self):
        """
        List candidate keys in the store by name.

        :return:
        """
        return self.__get_keys_by_status(self.STATUS_CANDIDATE)

    def get_accepted(self):
        """
        List accepted keys in the store by name.

        :return:
        """
        return self.__get_keys_by_status(self.STATUS_ACCEPTED)

    def get_rejected(self):
        """
        List rejected keys in the store by name.

        :return:
        """
        return self.__get_keys_by_status(self.STATUS_REJECTED)

    def get_denied(self):
        """
        List denied keys in the store by name.

        :return:
        """
        return self.__get_keys_by_status(self.STATUS_DENIED)

    @orm.db_session
    def add(self, pubkey_pem, hostname, machine_id):
        """
        Add PEM key to the store.

        :param pubkey_pem:
        :return:
        """
        self._lock_transation()
        StoredKey(hostname=hostname, fingerprint=Crypto.get_finterprint(pubkey_pem),
                  machine_id=machine_id, filename="{}.bin".format(os.path.join(self.__keys_path, machine_id)),
                  status=self.STATUS_CANDIDATE)
        self.__commit()

    @orm.db_session
    def delete(self, fingerprint):
        """
        Delete PEM key from the store.

        :param pubkey_pem:
        :return:
        """
        self._lock_transation()
        key = StoredKey.get(fingerprint=fingerprint)
        if key is not None:
            orm.delete(k for k in StoredKey if k.fingerprint == fingerprint)
            # delete key from the fs too
        self._unlock_transaction()

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
        params = {}
        if hostname:
            params['hostname'] = hostname
        if fingerprint:
            params['fingerprint'] = fingerprint
        key = StoredKey.get(**params)
        if key is not None:
            key.status = self.STATUS_REJECTED
        self._unlock_transaction()

    @orm.db_session
    def deny(self, fingerprint):
        """
        Deny key by fingerprint.

        :param fingerprint:
        :return:
        """
        self._lock_transation()
        key = StoredKey.get(fingerprint=fingerprint)
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
        try:
            key = StoredKey.get(fingerprint=fingerprint)
            if key is not None:
                key.status = self.STATUS_ACCEPTED
            else:
                raise sugar.lib.exceptions.SugarKeyStoreException("Key not found with the fingerprint {}".format(fingerprint))
        finally:
            self._unlock_transaction()

    @orm.db_session
    def get_key_by_fingerprint(self, fingerprint):
        """
        Get key by fingerprint.

        :param fingerprint:
        :return:
        """
        return orm.select(k for k in StoredKey if k.fingerprint == fingerprint)

    @orm.db_session
    def get_key_by_machine_id(self, machine_id):
        """
        Get key by name.

        :param name:
        :return: Usability status (boolean), key
        """
        return orm.select(k for k in StoredKey if k.machine_id == machine_id)

    @orm.db_session
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

    def clone(self):
        """
        Clone itself into the serialisable object.

        :return:
        """
        export_obj = Serialisable()
        for attr in self.__class__.__dict__:
            if not attr.startswith('_') and not callable(self.__class__.__dict__[attr]):
                setattr(export_obj, attr, getattr(self, attr))
        return export_obj


if __name__ == '__main__':
    ks = KeyStore("/tmp/ks")
    #c = Crypto()
    #pri, pub = c.create_rsa_keypair()
    #ks.add(pub, "bla", "blabla")
    from sugar.transport.serialisable import ObjectGate
    for x in ks.get_rejected():
        print(ObjectGate(x).pack())

    ks.reject(fingerprint='5a:fb:17:c8:a0:a5:7c:19:bd:14:9f:3c:52:de:b4:15:b2:d4:d7:0d:1b:50:cd:ca:8c:3b:21:cc:2e:d9:17:39')
