# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

import os
from twisted.internet import reactor, ssl

from autobahn.twisted.websocket import listenWS
from sugar.components.server.protocols import (SugarServerProtocol, SugarServerFactory,
                                               SugarConsoleServerProtocol, SugarConsoleServerFactory)
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger


class SugarServer(object):
    """
    Sugar Server.
    """
    def __init__(self):
        """
        Initialise Sugar Server class
        """
        self.config = get_config()
        self.log = get_logger(self)

        self.factory = SugarServerFactory("wss://*:5505")
        self.factory.protocol = SugarServerProtocol

        self.console_factory = SugarConsoleServerFactory("wss://*:5507")
        self.console_factory.protocol = SugarConsoleServerProtocol

    def on_shutdown(self):
        """
        Perform actions on shutdown.

        :return:
        """
        self.factory.core.master_local_token.cleanup()

    def run(self):
        """
        Run Sugar Server.
        :return:
        """
        self.factory.core.system.on_startup()
        context_factory = ssl.DefaultOpenSSLContextFactory(
            os.path.join(self.config.config_path, "ssl", "key.pem"),
            os.path.join(self.config.config_path, "ssl", "certificate.pem"),
        )

        listenWS(self.factory, context_factory)
        listenWS(self.console_factory, context_factory)

        reactor.addSystemEventTrigger("before", "shutdown", self.on_shutdown)
        reactor.run()
