"""
Key manager component (CLI)
"""

from __future__ import unicode_literals, absolute_import, print_function

import os
import sys
from collections import OrderedDict
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki.keystore import KeyStore
from sugar.lib.outputters.console import IterableOutput, TitleOutput


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
        self.__keystore = KeyStore(os.path.abspath(self.args.config_dir))

        self._list_output = IterableOutput(colors=self.config.terminal.colors,
                                           encoding=self.config.terminal.encoding)
        self._list_output._symbols_utf["n/a"] = self._list_output._symbols_ascii["n/a"] = "   No keys"

    def list(self):
        """
        List keys by status.
        Possible statuses:


        :return:
        """
        title = TitleOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        all = [("accepted", "success"), ("rejected", "alert"), ("denied", "warning"), ("new", "info")]
        ret = OrderedDict()

        for section in all:
            text, style = section
            if self.args.status == "all" or self.args.status == text:
                ret[text] = getattr(self.__keystore, "get_{}".format(text))()
                title.add(text.title(), style)

        # Short version
        for text in ret:
            sys.stdout.write(title.paint(text.title()) + "\n")
            sys.stdout.write(self._list_output.paint(ret[text]) + "\n\n")

        # Full version


    def run(self):
        """
        Run key manager

        :return:
        """
        self.log.debug("Running Key Manager")
        getattr(self, self.args.command)()
