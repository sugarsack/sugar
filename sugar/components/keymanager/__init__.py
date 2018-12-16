"""
Key manager component (CLI)
"""

from __future__ import unicode_literals, absolute_import, print_function

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki.keystore import KeyStore


class SugarKeyManager(object):
    """
    Sugar key manager CLI program.
    """
    OPERATION = ["accept", "deny", "reject", "list"]
    def __init__(self, args):
        """
        Init
        :param url:
        """
        self.config = get_config()
        self.args = args
        self.log = get_logger(self)
        self.__keystore = KeyStore(self.config.keystore)

    def list_keys(self, status="all"):
        """
        List keys by status.
        Possible statuses:


        :return:
        """



    def run(self):
        """
        Run key manager

        :return:
        """
        self.log.debug(self.args)
        print('blet')
