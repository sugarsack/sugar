"""
General runtime utilities.
"""
from __future__ import absolute_import, unicode_literals

import tempfile
import hashlib
import os

import sugar.utils.stringutils
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton

log = get_logger(__name__)


@Singleton
class MasterLocalToken(object):
    """
    Master token for local connections.
    """

    def __init__(self):
        """
        Creates master local token.

        :param path:
        """
        self._filename = tempfile.mktemp(".token", ".sugar.")
        with os.fdopen(os.open(self._filename, os.O_WRONLY | os.O_CREAT, 0o600), "wb") as fh:
            fh.write(sugar.utils.stringutils.to_bytes(hashlib.sha256(os.urandom(0xfff)).hexdigest()))

    def get_token(self):
        """
        Get token from the disk.

        :return:
        """
        with open(self._filename) as fh:
            return fh.read().strip()

    def cleanup(self):
        """
        Remove token file.

        :return:
        """
        try:
            os.remove(self._filename)
        except Exception as ex:
            log.error("General error while removing token file: {}".format(ex))
