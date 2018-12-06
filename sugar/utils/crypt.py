# coding: utf-8

"""
Crypto utils
"""
from __future__ import absolute_import, print_function, unicode_literals

import hashlib
try:
    import bcrypt
except ImportError:
    bcrypt = None


def hash_password(password):
    '''
    String to the salted crypted hash or just SHA256 hex digest, if no bcrypt around.
    '''
    if bcrypt is not None:
        pwd = bcrypt.hashpw(password, bcrypt.gensalt())
    else:
        pwd = hashlib.sha256(password.encode(encoding='utf_8', errors='strict')).hexdigest()

    return pwd


def check_password(password, hashed):
    '''
    Check if an attempt password is the same as hashed.
    '''
    if bcrypt is not None:
        res = bcrypt.hashpw(password, hashed) == hashed
    else:
        res = hash_password(password) == hashed

    return res
