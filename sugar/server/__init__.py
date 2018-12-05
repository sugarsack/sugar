# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

from twisted.internet import reactor, ssl

import txaio
from autobahn.twisted.websocket import listenWS
from sugar.server.protocols import SugarServerProtocol, SugarServerFactory

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
        txaio.start_logging(level='debug')
        self.factory = SugarServerFactory(u"wss://127.0.0.1:9000")
        self.factory.protocol = SugarServerProtocol

    def run(self):
        """
        Run Sugar Server.
        :return:
        """
        contextFactory = ssl.DefaultOpenSSLContextFactory('key.pem', 'certificate.pem')
        listenWS(self.factory, contextFactory)
        reactor.run()
