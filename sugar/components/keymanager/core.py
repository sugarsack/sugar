"""
Key manager core.
"""
from __future__ import absolute_import, unicode_literals
from sugar.utils.tokens import MasterLocalToken
from sugar.lib.compat import queue


class KeyManagerCore(object):
    """
    KeyManager commands.
    """
    def __init__(self, factory):
        self.local_token = MasterLocalToken()
        self.factory = factory
        self._queue = queue.Queue()

    def get_commands(self):
        """
        Get CLI command and send to the master.

        :return:
        """
        while True:
            try:
                yield self._queue.get(True, 0)
            except queue.Empty:
                break

