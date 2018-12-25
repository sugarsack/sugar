"""
Keymanager protocols
"""
from __future__ import absolute_import, unicode_literals

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory

from sugar.components.keymanager.core import KeyManagerCore
from sugar.transport import KeymanagerMsgFactory, ServerMsgFactory, any_binary


class SugarKeymanagerProtocol(WebSocketClientProtocol):
    """
    Sugar keymanager protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.debug("Keymanager connected: {0}".format(response.peer))

    def onOpen(self):
        msg_obj = self.factory.core.get_command()

    def onMessage(self, payload, binary):
        self.factory.reactor.stop()

    def onClose(self, wasClean, code, reason):
        self.log.debug("Socket closed: {0}".format(reason))


class SugarKeymanagerFactory(WebSocketClientFactory, ClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarKeymanagerProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.core = KeyManagerCore(self)
        self.maxDelay = 10

    def clientConnectionFailed(self, connector, reason):
        """

        :param connector:
        :param reason:
        :return:
        """
        self.log.error('Cannot connect keymanager. Is Master running?')
        self.reactor.stop()
