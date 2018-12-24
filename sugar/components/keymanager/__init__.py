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
from sugar.lib.outputters.console import IterableOutput, TitleOutput, Highlighter, ConsoleMessages
from sugar.lib import exceptions
import sugar.utils.console


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
        self._keystore = KeyStore(os.path.abspath(self.config.config_path))
        self.cli = ConsoleMessages(colors=self.config.terminal.colors,
                                   encoding=self.config.terminal.encoding)

        self._list_output = IterableOutput(colors=self.config.terminal.colors,
                                           encoding=self.config.terminal.encoding)
        self._list_output._symbols_utf["n/a"] = self._list_output._symbols_ascii["n/a"] = "   No keys"

        url = 'wss://{h}:{p}'.format(h='localhost', p=5507)
        self.factory = SugarKeymanagerFactory(url)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def list(self):
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
                for host_key in getattr(self._keystore, "get_{}".format(text))():
                    out.append({host_key.hostname: host_key.fingerprint})
                ret[text] = out
                title_output.add(text.title(), style)

        if self.args.format == "short":
            for text in ret:
                sys.stdout.write(title_output.paint(text.title()) + "\n")
                sys.stdout.write(self._list_output.paint(ret[text]) + "\n\n")
        elif self.args.format == "full":
            self.cli.error("Not *just yet*! :-)")
        else:
            raise exceptions.SugarConsoleException("Unknown format: {}".format(self.args.format))

    def accept(self):
        """
        Accept keys

        :return:
        """
        if not self.args.fingerprint and not self.args.hostname and not self.args.match_all_keys_at_once:
            sys.stderr.write("Error: please specify fingerprint or hostname or decide to match all keys atonce.\n")
            sys.exit(1)

        by_type = ""
        keys = []
        if self.args.fingerprint:
            by_type = "by fingerprint or part of it"
            keys = [key for key in self._keystore.get_key_by_fingerprint(self.args.fingerprint)
                    if key.status != KeyStore.STATUS_ACCEPTED]
        elif self.args.hostname:
            by_type = "by hostname"
            keys = [key for key in self._keystore.get_key_by_hostname(self.args.hostname)
                    if key.status != KeyStore.STATUS_ACCEPTED]
        elif self.args.match_all_keys_at_once:
            by_type = "accepting in batch"
            self.cli.warning("Dangerous mode")
            if sugar.utils.console.get_yn_input("Are you sure?"):
                keys = [key for key in self._keystore.get_new() if key.status != KeyStore.STATUS_ACCEPTED]
        if keys:
            connectWS(self.factory, ssl.ClientContextFactory())
            reactor.run()
            self.cli.info("Accepting {} key{} ({}):", len(keys), len(keys)> 1 and "s" or "", by_type)
            for key in keys:
                self._keystore.accept(key.fingerprint)
                self.cli.info("- {}... ({})", key.fingerprint[:29], key.hostname)
        else:
            self.cli.warning("*No keys* is matching your criteria.")

    def run(self):
        """
        Run key manager

        :return:
        """
        self.log.debug("Running Key Manager")
        getattr(self, self.args.command)()
