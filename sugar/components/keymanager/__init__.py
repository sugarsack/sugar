"""
Key manager component (CLI)
"""

from __future__ import unicode_literals, absolute_import, print_function

import os
import sys
from collections import OrderedDict

from autobahn.twisted.websocket import connectWS
from twisted.internet import reactor, ssl

from sugar.config import get_config
from sugar.components.keymanager.protocols import SugarKeymanagerProtocol, SugarKeymanagerFactory
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki.keystore import KeyStore
from sugar.lib.outputters.console import IterableOutput, TitleOutput, Highlighter
from sugar.lib import exceptions


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
        if not self.config.config_path:
            raise exceptions.SugarConfigurationException("Configuration not found")

        self.args = args
        self.log = get_logger(self)
        self.__keystore = KeyStore(os.path.abspath(self.config.config_path))

        self._list_output = IterableOutput(colors=self.config.terminal.colors,
                                           encoding=self.config.terminal.encoding)
        self._list_output._symbols_utf["n/a"] = self._list_output._symbols_ascii["n/a"] = "   No keys"

        url = 'wss://{h}:{p}'.format(h='localhost', p=5507)

        self.log.debug('Socket ')
        self.factory = SugarKeymanagerFactory(url)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def list(self) -> bool:
        """
        List keys by status.
        Possible statuses:


        :return:
        """
        title_output = TitleOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        all = [("accepted", "success"), ("rejected", "alert"), ("denied", "warning"), ("new", "info")]
        ret = OrderedDict()

        for section in all:
            text, style = section
            if self.args.status == "all" or self.args.status == text:
                out = []
                for host_key in getattr(self.__keystore, "get_{}".format(text))():
                    out.append({host_key.hostname: host_key.fingerprint})
                ret[text] = out
                title_output.add(text.title(), style)

        if self.args.format == "short":
            for text in ret:
                sys.stdout.write(title_output.paint(text.title()) + "\n")
                sys.stdout.write(self._list_output.paint(ret[text]) + "\n\n")
        elif self.args.format == "full":
            print("Not yet :-)")
        else:
            raise exceptions.SugarConsoleException("Unknown format: {}".format(self.args.format))


    def run(self):
        """
        Run key manager

        :return:
        """
        self.log.debug("Running Key Manager")
        getattr(self, self.args.command)()


        #connectWS(self.factory, ssl.ClientContextFactory())
        #reactor.run()
