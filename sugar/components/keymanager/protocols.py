"""
Keymanager protocols
"""
from __future__ import absolute_import, unicode_literals

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory

from sugar.components.keymanager.core import KeyManagerCore
from sugar.transport import KeymanagerMsgFactory


class SugarKeymanagerProtocol(WebSocketClientProtocol):
    """
    Sugar keymanager protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.debug("Keymanager connected: {0}".format(response.peer))

    def onOpen(self):
        for key in self.factory.core.get_changed_keys():
            key_message = KeymanagerMsgFactory().create()
            key_message.internal = key
            key_message.token = self.factory.core.local_token.get_token()
            self.sendMessage(KeymanagerMsgFactory.pack(key_message), isBinary=True)

    def onMessage(self, payload, binary):  # pylint: disable=W0613
        self.factory.reactor.stop()

    def onClose(self, wasClean, code, reason):
        self.log.debug("Socket closed: {0}".format(reason))

    def connectionLost(self, reason):
        try:
            self.factory.reactor.stop()
        except Exception:
            pass


class SugarKeymanagerFactory(WebSocketClientFactory, ClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarKeymanagerProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.core = KeyManagerCore(self)
        self.maxDelay = 10  # pylint: disable=C0103

    def clientConnectionFailed(self, connector, reason):
        """

        :param connector:
        :param reason:
        :return:
        """
        self.log.error('Cannot connect keymanager. Is Master running?')
        self.reactor.stop()
