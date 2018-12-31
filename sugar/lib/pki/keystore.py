"""
Testing peewee
"""

from __future__ import absolute_import, unicode_literals, print_function

import os
import time

from pony import orm

from sugar.lib.pki import Crypto
from sugar.lib import six
from sugar.utils.cli import get_current_component
import sugar.utils.files
import sugar.utils.stringutils
import sugar.lib.exceptions
from sugar.transport.serialisable import Serialisable


class KeyDB(object):
    """
    Key database.
    """
    DBFILE = "keystore.db"
    db = orm.Database()
    _instance = None

    def __init__(self, path):
        if self._instance is None:
            self.db.bind(provider="sqlite", filename=os.path.join(path, self.DBFILE), create_db=True)
            self.db.generate_mapping(create_tables=True)
            self._instance = self
        else:
            raise Exception("Should be getting instance instead")

    @classmethod
    def get_instance(cls, path):
        """
        Get KeyDB instance.

        :param path:
        :return:
        """
        # pylint: disable=W0212
        instance = KeyDB._instance
        if instance is None:
            instance = KeyDB(path)._instance
        # pylint: enable=W0212

        return instance


class StoredKey(KeyDB.db.Entity):
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


class KeyStore(object):
    """
    Key Store implementation with the SQLite3.
    """
    STATUS_CANDIDATE = "candidate"
    STATUS_ACCEPTED = "accepted"
    STATUS_DENIED = "denied"
    STATUS_REJECTED = "rejected"
    STATUS_INVALID = "invalid"  # Usually set on signature verification failure on responses

    LOCKFILE = ".keystore.lck"

    def __init__(self, path):
        """
        Constructor.

        :param dbpath:
        """
        path = os.path.join(path or "/etc/sugar", "pki")
        self.__component = get_current_component()

        if self.__component != 'local':
            self.__root_path = os.path.join(path, self.__component)
            self.__keys_path = sugar.utils.files.mk_dirs(os.path.join(self.__root_path, 'keys'))
        self.__lock_file_path = os.path.join(self.__root_path, self.LOCKFILE)
        self.__is_locked = False
        KeyDB.get_instance(self.__root_path)

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

    @staticmethod
    def __clone_rs(dbr):
        """
        Detach db session.

        :param dbr:
        :return:
        """
        return [obj.clone() for obj in dbr]

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

    @staticmethod
    @orm.db_session
    def __get_keys_by_status(status):
        """
        Get keys by status.

        :param status:
        :return:
        """
        ret = []
        for obj in orm.select(k for k in StoredKey if k.status == status):
            ret.append(obj.clone())

        return ret

    def get_key_pem(self, key: StoredKey) -> str:
        """
        Retrieve PEM key from the FS.

        :param key:
        :return:
        """
        self._lock_transation()
        try:
            with open(key.filename, "r") as key_fh:
                pem = key_fh.read()
        except Exception:
            pem = ""
        self._unlock_transaction()

        if not pem:
            raise sugar.lib.exceptions.SugarKeyStoreException("Broken key! Key PEM data not found.")

        return pem

    def get_new(self):
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
    def add(self, pubkey_pem: str, hostname: str, machine_id: str):
        """
        Add PEM key to the store.

        :param pubkey_pem:
        :param hostname:
        :param machine_id:
        :return:
        """
        self._lock_transation()
        filename = "{}.pem".format(os.path.join(self.__keys_path, machine_id))
        with open(filename, "wb") as rsa_pem_h:
            pubkey_pem = sugar.utils.stringutils.to_bytes(pubkey_pem)
            rsa_pem_h.write(pubkey_pem)
            StoredKey(hostname=hostname, fingerprint=Crypto.get_finterprint(pubkey_pem),
                      machine_id=machine_id, filename=filename, status=self.STATUS_CANDIDATE)
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
            if os.path.exists(key.filename):
                os.remove(key.filename)
                orm.delete(k for k in StoredKey if k.fingerprint == fingerprint)
            else:
                raise OSError("File '{}' not found".format(key.filename))
        self._unlock_transaction()

    @orm.db_session
    def reject(self, fingerprint, hostname=None) -> str:
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
        params['fingerprint'] = fingerprint
        key = StoredKey.get(**params)
        if key is not None:
            key.status = self.STATUS_REJECTED
            orm.commit()
        self._unlock_transaction()
        return self.STATUS_REJECTED

    @orm.db_session
    def deny(self, fingerprint) -> str:
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
        return self.STATUS_DENIED

    @orm.db_session
    def accept(self, fingerprint) -> str:
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
        return self.STATUS_ACCEPTED

    @orm.db_session
    def get_key_by_fingerprint(self, fingerprint):
        """
        Get key by fingerprint.

        :param fingerprint:
        :return:
        """
        return self.__clone_rs(orm.select(k for k in StoredKey
                                          if k.fingerprint.startswith(sugar.utils.stringutils.to_str(fingerprint))))

    @orm.db_session
    def get_key_by_machine_id(self, machine_id):
        """
        Get key by name.

        :param name:
        :return: Usability status (boolean), key
        """
        return self.__clone_rs(orm.select(k for k in StoredKey
                                          if k.machine_id == sugar.utils.stringutils.to_str(machine_id)))

    @orm.db_session
    def get_key_by_hostname(self, hostname):
        """
        Get key by hostname.

        :param hostname:
        :return:
        """
        return self.__clone_rs(orm.select(k for k in StoredKey
                                          if k.hostname == sugar.utils.stringutils.to_str(hostname)))


if __name__ == '__main__':
    ks = KeyStore("/tmp/ks")
    #c = Crypto()
    #pri, pub = c.create_rsa_keypair()
    #ks.add(pub, "bla", "blabla")
    from sugar.transport.serialisable import ObjectGate
    for x in ks.get_rejected():
        print(ObjectGate(x).pack())

    ks.reject(fingerprint='5a:fb:17:c8:a0:a5:7c:19:bd:14:9f:3c:52:de:b4:15:b2:d4:d7:0d:1b:50:cd:ca:8c:3b:21:cc:2e:d9:17:39')
