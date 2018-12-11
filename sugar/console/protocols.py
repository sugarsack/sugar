# coding: utf-8

"""
Console protocols
"""

from __future__ import absolute_import, unicode_literals, print_function

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory


class SugarConsoleProtocol(WebSocketClientProtocol):
    """
    Sugar client protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.debug("Console connected: {0}".format(response.peer))

    def onOpen(self):
        self.log.debug("Opened socket")
        self.sendMessage('ku ku'.encode('utf-8'))

    def onMessage(self, payload, binary):
        if binary:
            self.log.info("Binary message received: {0} bytes".format(len(payload)))
        else:
            self.log.info("Text message received: {0}".format(payload.decode('utf8')))
        self.factory.reactor.stop()

    def onClose(self, wasClean, code, reason):
        self.log.debug("Socket closed: {0}".format(reason))


class SugarClientFactory(WebSocketClientFactory, ClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarConsoleProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.maxDelay = 10

    def clientConnectionFailed(self, connector, reason):
        """

        :param connector:
        :param reason:
        :return:
        """
        self.log.error('Cannot connect console. Is Master running?')
        self.console.parse_command_line()
        self.reactor.stop()
