"""
Sugar client and server protocols.
"""

from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import (WebSocketServerProtocol,
                                        WebSocketClientProtocol,
                                        WebSocketClientFactory,
                                        WebSocketServerFactory)
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


# ######################################
# SERVER
# ######################################


class SugarServerProtocol(WebSocketServerProtocol):
    """
    Sugar server protocol.
    """
    def onConnect(self, request):
        self.log.info("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        self.factory.register(self)
        self.log.info("WebSocket connection open")

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.log.info("Binary message received: {0} bytes".format(len(payload)))
        else:
            self.log.info("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.log.info("WebSocket connection closed: {0}".format(reason))

    def connectionLost(self, reason):
        """
        Client connection dies.
        :param reason:
        :return:
        """
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class SugarServerFactory(WebSocketServerFactory):
    """
    Server factory.
    """
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []  # More smarter stuff here to select clients

    def register(self, client):
        """
        Register client.

        :param client:
        :return:
        """
        if client not in self.clients:
            self.log.info("Registering client: {}".format(client))
            self.clients.append(client)

    def unregister(self, client):
        """
        Remove client from the registry.

        :param client:
        :return:
        """
        if client in self.clients:
            self.log.info("Unregistering client: {}".format(client))
            self.clients.remove(client)
