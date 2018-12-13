"""
Signing, crypt/decrypt, auth...
"""
from __future__ import absolute_import, print_function, unicode_literals


from io import BytesIO
import hashlib
import zlib
import pickle
from sugar.lib import six

try:
    from Crypto.Hash import SHA256
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto import Random
except ImportError:
    PKCS1_v1_5 = RSA = SHA256  = None

try:
    from Crypto.Random import get_random_bytes
except ImportError:
    get_random_bytes = None

try:
    from Crypto.Cipher import AES, PKCS1_OAEP
except ImportError:
    PKCS1_OAEP = AES = None


from sugar.lib import exceptions


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

    def blah(self):
        message = b"I want this stream signed"
        digest = SHA256.new()
        digest.update(message)

        # Read shared key from file
        private_key = False
        with open ("private_key.pem", "r") as myfile:
            private_key = RSA.importKey(myfile.read())

        # Load private key and sign message
        signer = PKCS1_v1_5.new(private_key)
        sig = signer.sign(digest)

        # Load public key and verify message
        verifier = PKCS1_v1_5.new(private_key.publickey())
        verified = verifier.verify(digest, sig)
        assert verified, 'Signature verification failed'
        print('Successfully verified message')

    def create_rsa_keypair(self, bits=2048):
        """
        Generate an RSA keypair with an exponent of 65537 in PEM format
        param: bits The key length in bits

        Return private key and public key as bytes.

        :param bits:
        :return: tuple (private_key, public_key)
        """

        new_key = RSA.generate(bits, e=65537)
        return new_key.exportKey("PEM"), new_key.publickey().exportKey("PEM")

    def create_aes_key(self):
        """
        Make temporary share-able bi-directional key for AES session.

        :return:
        """
        if get_random_bytes is None:
            exceptions.SugarDependencyException("'Crypto.Random' seems missing")

        return get_random_bytes(0x10)

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

    def _unpad(self, data):
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
        if AES is None:
            raise exceptions.SugarDependencyException("AES algorithm is not available.")

        iv = Random.new().read(AES.block_size)
        out = BytesIO()
        for chunk in (iv, AES.new(self.key, AES.MODE_CBC, iv).encrypt(self._pad(data))):
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
        vi, data = [handle.read(x) for x in (16, -1)]
        return self._unpad(AES.new(self.key, AES.MODE_CBC, vi).decrypt(data))

    def encrypt_rsa(self, pubkey_pem, data):
        """
        Encrypt data with RSA public key in PEM format.

        :return:
        """

        if isinstance(data, six.text_type):
            data = data.encode("utf-8")
        encrypted = RSA.importKey(pubkey_pem).encrypt(data, 32)

        return isinstance(encrypted, (list, tuple)) and encrypted[0] or encrypted

    def decrypt_rsa(self, privkey_pem, data):
        """
        Decrypt data with RSA.

        :return:
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        return RSA.importKey(privkey_pem).decrypt(data)

    def sign(self, priv_key, data):
        """
        Sign data.

        :return: signature
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        digest = SHA256.new()
        digest.update(data)

        return PKCS1_v1_5.new(RSA.importKey(priv_key)).sign(digest)

    def verify_signature(self, pubkey_pem, data, signature):
        """
        Verify signature.

        :param pubkey:
        :param data:
        :param signature:
        :return:
        """
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")

        digest = SHA256.new()
        digest.update(data)

        return PKCS1_v1_5.new(RSA.importKey(pubkey_pem)).verify(digest, signature)

    def get_object_checksum(self, obj):
        """
        Get object checksum.

        :param obj:
        :return:
        """
        return zlib.crc32(pickle.dumps(obj))

    def get_finterprint(self, pubkey_pem, cs_alg='sha256'):
        """
        Pass in a raw pem string, and the type of cryptographic hash to use. The default is SHA256.
        The fingerprint of the pem will be returned.

        :param pubkey_pem:
        :param cs_alg: algorithm
        :return:
        """
        digest = getattr(hashlib, cs_alg)(pubkey_pem).hexdigest()
        return ':'.join(pre + pos for pre, pos in zip(digest[::2], digest[1::2]))
