# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

from twisted.internet import reactor, ssl

from autobahn.twisted.websocket import connectWS
from sugar.console.protocols import SugarConsoleProtocol, SugarClientFactory
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger

log = get_logger(__name__)

__author__ = "Bo Maryniuk"
__copyright__ = "Copyright 2018, Sugar Project"
__credits__ = []
__license__ = "Apache 2.0"
__version__ = "0.0.1"
__email__ = "bo@maryniuk.net"
__status__ = "Damn Bloody Alpha"


class SugarConsole(object):
    """
    Sugar console class.
    """

    def __init__(self):
        """
        Init
        :param url:
        """
        self.config = get_config()

        url = 'wss://{h}:{p}'.format(h='localhost', p=5507)

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
