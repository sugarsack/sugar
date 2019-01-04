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

SUFFIX = ".token"
PREFIX = ".sugar."


@Singleton
class MasterLocalToken(object):
    """
    Master token for local connections.
    """

    def __init__(self, filename=None):
        """
        Creates master local token.

        :param filename: filename, default to None
        """
        self.log = get_logger(__name__)
        self._filename = filename or tempfile.mktemp(SUFFIX, PREFIX)
        if not filename:  # New token needs to be created
            with os.fdopen(os.open(self._filename, os.O_WRONLY | os.O_CREAT, 0o600), "wb") as tmp_fh:
                tmp_fh.write(sugar.utils.stringutils.to_bytes(hashlib.sha256(os.urandom(0xfff)).hexdigest()))
        elif not os.path.exists(self._filename):
            raise OSError("Token file '{}' does not exists.".format(self._filename))

        self.__token = None

    def get_token(self):
        """
        Get token from the disk.

        :return: Token string
        """
        if self.__token is None:
            with open(self._filename) as tkn_fh:
                self.__token = tkn_fh.read().strip()
        return self.__token

    def cleanup(self):
        """
        Remove token file.

        :return: None
        """
        try:
            os.remove(self._filename)
        except Exception as exc:
            self.log.error("General error while removing token file: {}".format(exc))


def get_probable_token_filename(directory="/tmp"):
    """
    Try to get possible filename

    :param directory: root path
    :return: path string
    """
    files = {}
    for filename in os.listdir(directory):
        if filename.startswith(PREFIX) and filename.endswith(SUFFIX):
            path = os.path.join(directory, filename)
            files[os.path.getctime(path)] = path
    try:
        path = files[max(files)]
    except ValueError:
        path = None

    return path
