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


__author__ = "Bo Maryniuk"
__copyright__ = "Copyright 2018, Sugar Project"
__credits__ = []
__license__ = "Apache 2.0"
__version__ = "0.0.1"
__email__ = "bo@maryniuk.net"
__status__ = "Damn Bloody Alpha"


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

    def run(self):
        """
        Run Sugar Server.
        :return:
        """
        self.factory.core.system.on_startup()
        contextFactory = ssl.DefaultOpenSSLContextFactory(
            os.path.join(self.config.config_path, "ssl", "key.pem"),
            os.path.join(self.config.config_path, "ssl", "certificate.pem"),
        )

        listenWS(self.factory, contextFactory)
        listenWS(self.console_factory, contextFactory)

        reactor.run()
