"""
Keystore and clients db.
"""
from __future__ import absolute_import, print_function, unicode_literals


class Key(object):
    """
    Machine public key. It is assigned to the specific unique ID of the machine.
    """
    def __init__(self, pubkey_pem):
        """
        Key container object.

        :param pubkey_pem: Public key (PEM)
        """
        self.__pem = pubkey_pem
        self.__name = None
        self.__fingerprint = None

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


class KeyStore(object):
    """
    KeyStore class.
    """
    def __init__(self, path):
        """
        Keystore main class.

        :param path: Path to the keystore.
        """

    def list(self):
        """
        List keys in the store.

        :return:
        """

    def add(self, key):
        """
        Add key to the store.

        :param key:
        :return:
        """

    def delete(self, key):
        """
        Delete key from the store.

        :param key:
        :return:
        """
