# coding: utf-8

"""
Server protocols
"""

from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory


class SugarConsoleServerProtocol(WebSocketServerProtocol):
    """
    Console protocol for server.
    """
    def onConnect(self, request):
        self.log.info("Console connected: {0}".format(request.peer))

    def onOpen(self):
        self.factory.register(self)
        self.log.info("Console WebSocket connection established")

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.log.info("Binary message received: {0} bytes".format(len(payload)))
        else:
            self.log.info("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.log.info("Console WebSocket connection has been terminated: {0}".format(reason))

    def connectionLost(self, reason):
        """
        Client connection dies.
        :param reason:
        :return:
        """
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class SugarConsoleServerFactory(WebSocketServerFactory):
    """
    Server control console factory.
    """
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.consoles = []  # More smarter stuff here to select clients

    def register(self, client):
        """
        Register control console.

        :param client:
        :return:
        """
        if client not in self.consoles:
            self.log.info("Registering console: {}".format(client))
            self.consoles.append(client)

    def unregister(self, client):
        """
        Remove control console from the registry.

        :param client:
        :return:
        """
        if client in self.consoles:
            self.log.info("Unregistering console: {}".format(client))
            self.consoles.remove(client)


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
