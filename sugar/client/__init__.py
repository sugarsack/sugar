"""
Sugar client
"""

import sys

from twisted.internet import reactor, ssl

from autobahn.twisted.websocket import connectWS
from sugar.client.protocols import SugarClientFactory
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger

log = get_logger(__name__)


class SugarClient(object):
    """
    Sugar client class.
    """

    def __init__(self):
        """
        Init
        :param url:
        """
        self.config = get_config()
        url = None

        # TODO: cluster connect
        for target in self.config.master:
            url = 'wss://{h}:{p}'.format(h=target.hostname, p=target.ctrl_port)
            break

        log.debug('Socket ')
        self.factory = SugarClientFactory(url)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def run(self):
        """
        Run client.
        :return:
        """
        connectWS(self.factory, ssl.ClientContextFactory())
        reactor.run()
