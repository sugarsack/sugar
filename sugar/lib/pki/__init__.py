"""
Signing, crypt/decrypt, auth...
"""
from __future__ import absolute_import, print_function, unicode_literals


from io import BytesIO

import hashlib
import zlib
import pickle
from sugar.lib import six
from sugar.lib import exceptions

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto import Random

try:
    import bcrypt
except ImportError:
    bcrypt = None


class Crypto(object):
    """
    Crypto class.
    """
    BLOCK_SIZE = 16  # Bytes

    def __init__(self, key=None):
        if key:
            if isinstance(key, six.string_types):
                key = key.encode("utf-8")
            self.key = hashlib.sha256(key).hexdigest()
        else:
            self.key = self.create_aes_key()

    @staticmethod
    def create_rsa_keypair(bits=2048):
        """
        Generate an RSA keypair with an exponent of 65537 in PEM format
        param: bits The key length in bits

        Return private key and public key as bytes.

        :param bits:
        :return: tuple (private_key, public_key)
        """

        new_key = RSA.generate(bits, e=65537)
        return new_key.exportKey("PEM"), new_key.publickey().exportKey("PEM")

    @staticmethod
    def create_aes_key():
        """
        Make temporary share-able bi-directional key for AES session.

        :return:
        """
        return Random.get_random_bytes(0x10)

    def _pad(self, data):
        """
        Pad the data.

        :param data:
        :return:
        """
        padding = (self.BLOCK_SIZE - len(data) % self.BLOCK_SIZE) * chr(self.BLOCK_SIZE - len(data) % self.BLOCK_SIZE)

        if six.PY3 and isinstance(data, six.binary_type):
            padding = padding.encode('utf-8')

        return data + padding

    @staticmethod
    def _unpad(data):
        """
        Un-pad the data.

        :param data:
        :return:
        """
        return data[:-ord(data[len(data) - 1:])]

    def encrypt_aes(self, data):
        """
        Encrypt data with AES with EAX mode (verification for tampering).

        :return: Binary data
        """
        iv_pad = Random.new().read(AES.block_size)
        out = BytesIO()
        for chunk in (iv_pad, AES.new(self.key, AES.MODE_CBC, iv_pad).encrypt(self._pad(data))):
            out.write(chunk)
        out.seek(0)

        return out.read()

    def decrypt_aes(self, data):
        """
        Decrypt data with AES with EAX mode (verification for tampering).

        :return:
        """
        if AES is None:
            raise exceptions.SugarDependencyException("AES algorithm is not available.")

        handle = BytesIO(data)
        iv_pad, data = [handle.read(x) for x in (16, -1)]
        return self._unpad(AES.new(self.key, AES.MODE_CBC, iv_pad).decrypt(data))

    @staticmethod
    def encrypt_rsa(pubkey_pem, data):
        """
        Encrypt data with RSA public key in PEM format.

        :return:
        """

        if isinstance(data, six.text_type):
            data = data.encode("utf-8")
        encrypted = RSA.importKey(pubkey_pem).encrypt(data, 32)

        return isinstance(encrypted, (list, tuple)) and encrypted[0] or encrypted

    @staticmethod
    def decrypt_rsa(privkey_pem, data):
        """
        Decrypt data with RSA.

        :return:
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        return RSA.importKey(privkey_pem).decrypt(data)

    @staticmethod
    def sign(priv_key, data):
        """
        Sign data.

        :return: signature
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        digest = SHA256.new()
        digest.update(data)

        return PKCS1_v1_5.new(RSA.importKey(priv_key)).sign(digest)

    @staticmethod
    def verify_signature(pubkey_pem: str, data: str, signature: str) -> bool:
        """
        Verify signature.

        :param pubkey_pem:
        :param data:
        :param signature:
        :return:
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        digest = SHA256.new()
        digest.update(data)

        return PKCS1_v1_5.new(RSA.importKey(pubkey_pem)).verify(digest, signature)

    @staticmethod
    def get_object_checksum(obj):
        """
        Get object checksum.

        :param obj:
        :return:
        """
        return zlib.crc32(pickle.dumps(obj))

    @staticmethod
    def get_finterprint(pubkey_pem, cs_alg='sha256'):
        """
        Pass in a raw pem string, and the type of cryptographic hash to use. The default is SHA256.
        The fingerprint of the pem will be returned.

        :param pubkey_pem:
        :param cs_alg: algorithm
        :return:
        """
        digest = getattr(hashlib, cs_alg)(pubkey_pem).hexdigest()
        return ':'.join(pre + pos for pre, pos in zip(digest[::2], digest[1::2]))

    @staticmethod
    def hash_password(password):
        """
        String to the salted crypted hash or just SHA256 hex digest, if no bcrypt around.
        """
        if bcrypt is not None:
            pwd = bcrypt.hashpw(password, bcrypt.gensalt())
        else:
            pwd = hashlib.sha256(password.encode(encoding='utf_8', errors='strict')).hexdigest()

        return pwd

    @classmethod
    def check_password(cls, password, hashed):
        """
        Check if an attempt password is the same as hashed.
        """
        if bcrypt is not None:
            res = bcrypt.hashpw(password, hashed) == hashed
        else:
            res = cls.hash_password(password) == hashed

        return res

    @staticmethod
    def reinit_crypto():
        """
        When a fork arises, pycrypto needs to reinit
        From its doc::

            Caveat: For the random number generator to work correctly,
            you must call Random.atfork() in both the parent and
            child processes after using os.fork()

        """
        Random.atfork()
