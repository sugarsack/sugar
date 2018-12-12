# coding: utf-8

"""
Console protocols
"""

from __future__ import absolute_import, unicode_literals, print_function

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory

from sugar.transport import ObjectGate


class SugarConsoleProtocol(WebSocketClientProtocol):
    """
    Sugar client protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.debug("Console connected: {0}".format(response.peer))

    def onOpen(self):
        msg_obj = self.factory.console.get_task()
        self.sendMessage(ObjectGate(msg_obj).pack(True), isBinary=True)

    def onMessage(self, payload, binary):
        self.log.info('Response from the master accepted. Stopping.')
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
        self.reactor.stop()
