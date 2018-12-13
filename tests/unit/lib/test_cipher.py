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
