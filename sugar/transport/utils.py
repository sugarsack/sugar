"""
Transport utils (various).
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import time
import hashlib

from sugar.utils import stringutils
from sugar.lib import six


def gen_id():
    """
    Generate and ID for the protocol.

    :return:
    """
    bin_data = b'%s %s' %(stringutils.to_bytes(six.text_type(time.time())), os.urandom(0xff))
    return hashlib.sha256(bin_data).hexdigest()
