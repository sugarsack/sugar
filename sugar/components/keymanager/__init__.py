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
from sugar.components.keymanager.protocols import SugarKeymanagerFactory
from sugar.lib.logger.manager import get_logger
from sugar.lib.pki.keystore import KeyStore
from sugar.lib.outputters.console import IterableOutput, TitleOutput, ConsoleMessages
from sugar.lib import exceptions
import sugar.utils.console
import sugar.utils.exitcodes
import sugar.utils.data
from sugar.lib.i18n import gettext as __


class SugarKeyManager(object):
    """
    Sugar key manager CLI program.
    """
    OPERATION = ["accept", "deny", "reject", "list"]

    def __init__(self, args):
        """
        Init

        :param url:
        :raises: Exception if factory is not secure SSL
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
        self._list_output.symbols_utf["n/a"] = self._list_output.symbols_ascii["n/a"] = __("   No keys")

        url = 'wss://{h}:{p}'.format(h='localhost', p=5507)
        self.factory = SugarKeymanagerFactory(url)
        if not self.factory.isSecure:
            raise Exception('Unable to initialise TLS')

    def _format_keys(self, keys):
        """
        Format keys for the CLI output.

        :param keys: Keys to format.
        :return: list of dicts with the key data per each.
        """
        out = []
        for host_key in keys:
            if self.args.format == "short":
                out.append({host_key.hostname: host_key.fingerprint})
            else:
                out.append({
                    host_key.hostname: OrderedDict([
                        ("fingerprint", host_key.fingerprint),
                        ("machine-id", host_key.machine_id),
                        ("filename", host_key.filename),
                        ("notes", host_key.notes or "N/A")
                    ]),
                })
        return out

    def list(self):
        """
        List keys by status.
        Possible statuses:

        :return: None
        """
        title_output = TitleOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        all_sections = [("accepted", "success"), ("rejected", "alert"), ("denied", "warning"), ("new", "info")]
        ret = OrderedDict()

        if sugar.utils.data.how_many([self.args.fingerprint, self.args.hostname, self.args.machineid]) > 1:
            self.cli.error("You should specify either *fingerprint* or *hostname* or *machine ID*.")
            sys.exit(sugar.utils.exitcodes.EX_USAGE)
        elif sugar.utils.data.exactly_one([self.args.fingerprint, self.args.hostname, self.args.machineid]):
            if self.args.fingerprint:
                text, keys = "list by fingerprint", self._keystore.get_key_by_fingerprint(self.args.fingerprint)
            elif self.args.machineid:
                text, keys = "list by machine id", self._keystore.get_key_by_machine_id(self.args.machineid)
            else:
                text, keys = "list by host name", self._keystore.get_key_by_hostname(self.args.hostname)

            ret[text] = self._format_keys(keys)
            title_output.add(text.title(), "info")
        else:
            for section in all_sections:
                text, style = section
                if self.args.status == "all" or self.args.status == text:
                    ret[text] = self._format_keys(getattr(self._keystore, "get_{}".format(text))())
                    title_output.add(text.title(), style)

        for text in ret:
            sys.stdout.write(title_output.paint(text.title()) + "\n")
            sys.stdout.write(self._list_output.paint(ret[text]) + "\n\n")

    def _set_keys_status(self, status: str, doing: str, func: callable) -> list:
        """
        Match keys by criteria.

        :return: list of matched keys
        """
        by_type = ""
        keys = []
        if self.args.fingerprint:
            by_type = "by fingerprint or part of it"
            keys = [key for key in self._keystore.get_key_by_fingerprint(self.args.fingerprint) if key.status != status]
        elif self.args.hostname:
            by_type = "by hostname"
            keys = [key for key in self._keystore.get_key_by_hostname(self.args.hostname) if key.status != status]
        elif self.args.match_all_keys_at_once:
            by_type = "in batch"
            self.cli.warning("Dangerous mode!")
            if sugar.utils.console.get_yn_input("Are you sure?"):
                if self.args.command in ["accept", "reject", "deny"]:
                    keys = [key for key in self._keystore.get_new() if key.status != status]
                elif self.args.command == "delete":
                    for keyfunction in [self._keystore.get_rejected, self._keystore.get_denied, self._keystore.get_new]:
                        keys.extend([key for key in keyfunction() if key.status != status])
        if keys:
            self.log.debug("{} keys matching {} criteria", len(keys), by_type)
            self.cli.info("*{} {} key{}* ({}):", doing.title(), len(keys), len(keys) > 1 and "s" or "", by_type)
            for key in keys:
                key.status = func(key.fingerprint)  # The instance of this "key" is beyound the transaction.
                self.cli.info("  - {}... (*{}*)", key.fingerprint[:29], key.hostname)
                self.factory.core.add_key(key)
        else:
            self.cli.warning("*No keys* is matching your criteria.")

        return keys

    def send_to_master(self):
        """
        Send tasks to the master.

        When keys were status updated, connected peers
        should be instantly updated: connections dropped or accepted, etc.
        For this, message-per-key is dropped into the queue and then
        protocol sends these messages to the Master for further update.

        Protocol will shutdown reactor on its own from the Factory, once
        everything is sent and tasks are finished.

        :return: None
        """
        if self.factory.core.local_token is not None:
            self.log.debug("local token found of running master. Connecting...")
            connectWS(self.factory, ssl.ClientContextFactory())
            reactor.run()

    def accept(self):
        """
        Accept keys

        :return: list of accepted keys
        """
        self.log.debug("accepting keys")
        return self._set_keys_status(KeyStore.STATUS_ACCEPTED, "accepting", self._keystore.accept)

    def deny(self):
        """
        Deny specified keys.

        :return: list of denied keys
        """
        self.log.debug("denying keys")
        return self._set_keys_status(KeyStore.STATUS_DENIED, "denying", self._keystore.deny)

    def reject(self):
        """
        Reject specified keys.

        :return: list of rejected keys
        """
        self.log.debug("dejecting keys")
        return self._set_keys_status(KeyStore.STATUS_REJECTED, "rejecting", self._keystore.reject)

    def delete(self):
        """
        Delete specified keys (fingerprint only).
        Accepted keys cannot be deleted. They should be first denied or rejected.

        :return: list of deleted keys
        """
        self.log.debug("deleting keys")
        return self._set_keys_status(KeyStore.STATUS_ACCEPTED, "deleting", self._keystore.delete)

    def run(self):
        """
        Run key manager

        :return: None
        """
        self.log.debug("starting Key Manager")
        if (self.args.command not in ["list", "delete"]
                and not self.args.fingerprint
                and not self.args.hostname
                and not self.args.match_all_keys_at_once):
            self.cli.error("Error: please specify fingerprint or hostname or decide to match all keys at once.")
            self.log.debug("unknown key criteria (fingerprint or hostname or all) "
                           "while deleting or listing a key. Exiting.")
            sys.exit(1)

        elif self.args.command == "delete" and not sugar.utils.data.how_many([self.args.fingerprint,
                                                                              self.args.match_all_keys_at_once]):
            self.cli.error("Error: please specify fingerprint to delete a key.")
            self.log.debug("unknown key fingerprint while attempt to delete a key. Exiting.")
            sys.exit(1)

        if getattr(self, self.args.command)():
            self.log.debug("changes has been made, sending that to the Master.")
            self.send_to_master()
