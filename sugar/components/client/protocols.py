# coding: utf-8
"""
Client protocols
"""
from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ReconnectingClientFactory


class SugarClientProtocol(WebSocketClientProtocol):
    """
    Sugar client protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.info("Server connected: {0}".format(response.peer))

    def onOpen(self):
        self.log.info("WebSocket connection open")

        def hello():
            self.sendMessage(u"Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, hello)

        hello()

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.log.info("Binary message received: {0} bytes".format(len(payload)))
        else:
            self.log.info("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        self.log.info("WebSocket connection closed: {0}".format(reason))


class SugarClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarClientProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        ReconnectingClientFactory.__init__(self)
        self.maxDelay = 10

    def clientConnectionFailed(self, connector, reason):
        """
        On clonnection failed.

        :param connector:
        :param reason:
        :return:
        """
        self.log.info("Client connection failed .. retrying ..")
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        """
        On connection lost

        :param connector:
        :param reason:
        :return:
        """
        self.log.info("Client connection lost .. retrying ..")
        self.resetDelay()
        self.retry(connector)
