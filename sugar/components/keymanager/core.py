"""
Key manager core.
"""
from __future__ import absolute_import, unicode_literals

import os

from sugar.utils.tokens import MasterLocalToken, get_probable_token_filename
from sugar.lib.compat import queue


class KeyManagerCore(object):
    """
    KeyManager commands.
    """
    def __init__(self, factory):

        token_filename = get_probable_token_filename()
        if token_filename is None or not os.access(token_filename, os.R_OK):
            self.local_token = None
        else:
            self.local_token = MasterLocalToken(token_filename)
        self.factory = factory
        self._queue = queue.Queue()

    def add_key(self, key):
        """
        Add key for the master.

        :param command:
        :return:
        """
        self._queue.put_nowait(key)

    def get_changed_keys(self):
        """
        Get changed keys and send to the master.

        :return:
        """
        while True:
            try:
                yield self._queue.get(True, 0)
            except queue.Empty:
                break
