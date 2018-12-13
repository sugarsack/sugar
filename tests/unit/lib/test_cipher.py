"""
Test Crypto
"""

from __future__ import absolute_import, unicode_literals, print_function

import pytest
import pickle
from sugar.lib.pki import Crypto


class Foo(object):
    """
    An object.
    """
    def __init__(self):
        self.bar = "Fred"


@pytest.fixture
def crypto():
    """
    Crypto instance with a random key.

    :return:
    """
    return Crypto()


@pytest.fixture
def message():
    """
    Text message.

    :return:
    """
    return "That's easy to fix, but I can't be bothered."


@pytest.fixture
def bytecode():
    """
    An object instance
    :return:
    """
    return pickle.dumps(Foo())


class TestCrypto(object):
    """
    Test crypto object.
    """
    def test_aes_enc_dec_str(self, crypto, message):
        """
        Test AES encryption of a string.

        :return:
        """
        assert crypto.decrypt_aes(crypto.encrypt_aes(message)).decode('utf-8') == message

    def test_aes_enc_dec_object(self, crypto, bytecode):
        """
        Test AES encryption of a bytecode.

        :param crypto:
        :param bytecode:
        :return:
        """
        assert crypto.decrypt_aes(crypto.encrypt_aes(bytecode)) == bytecode
        obj = pickle.loads(bytecode)
        assert obj.bar == "Fred"

    def test_rsa_enc_dec_str(self, crypto, message):
        """
        Encrypt a string message using RSA pub/priv keypair.

        :param crypto:
        :param message:
        :return:
        """
        priv, pub = crypto.create_rsa_keypair()
        assert crypto.decrypt_rsa(priv, crypto.encrypt_rsa(pub, message)).decode('utf-8') == message

    def test_rsa_enc_dec_object(self, crypto, bytecode):
        """
        Encrypt an object
        :param crypto:
        :param bytecode:
        :return:
        """
        priv, pub = crypto.create_rsa_keypair()
        assert crypto.decrypt_rsa(priv, crypto.encrypt_rsa(pub, bytecode)) == bytecode
        obj = pickle.loads(bytecode)
        assert obj.bar == "Fred"

    def test_object_signature(self, crypto):
        """
        Test object signature.

        :param crypto:
        :return:
        """

        foo = Foo()
        foo.very = "important"

        csum = str(crypto.get_object_checksum(foo))
        priv, pub = crypto.create_rsa_keypair()
        signature = crypto.sign(priv, csum)

        assert crypto.verify_signature(pub, csum, signature)

    def test_object_signature_tampered(self, crypto):
        """
        Test object signature, while data was tampered.

        :param crypto:
        :return:
        """

        foo = Foo()
        foo.very = "important"

        csum = str(crypto.get_object_checksum(foo))
        priv, pub = crypto.create_rsa_keypair()
        signature = crypto.sign(priv, csum)

        foo.very = "tampered"
        csum = str(crypto.get_object_checksum(foo))

        assert not crypto.verify_signature(pub, csum, signature)

    def test_fingerprint(self, crypto):
        """
        Test fingerprint.

        :return:
        """
        fp = "85:73:8f:8f:9a:7f:1b:04:b5:32:9c:59:0e:bc:b9:e4:25:92:5c:6d:09:84:08:9c:43:a0:22:de:4f:19:c2:81"
        assert crypto.get_finterprint(b'whatever') == fp
