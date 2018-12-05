"""
Sugar client
"""

import sys

from twisted.python import log
from twisted.internet import reactor, ssl

from autobahn.twisted.websocket import connectWS
from sugar.proto import SugarClientFactory


class SugarClient(object):
    """
    Sugar client class.
    """

    def __init__(self, url="wss://127.0.0.1:9000"):
        """
        Init
        :param url:
        """
        self.factory = SugarClientFactory(url)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def run(self):
        """
        Run client.
        :return:
        """
        connectWS(self.factory, ssl.ClientContextFactory())
        log.startLogging(sys.stdout)
        reactor.run()
