# coding: utf-8

"""
Console protocols
"""

from __future__ import absolute_import, unicode_literals, print_function

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory

from sugar.transport import ConsoleMsgFactory, ServerMsgFactory, any_binary


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
        self.sendMessage(ConsoleMsgFactory.pack(msg_obj), isBinary=True)

    def onMessage(self, payload, binary):
        if binary:
            response = ServerMsgFactory.unpack(payload)
            self.log.info('Reply: {}'.format(response.ret.message))
            self.log.info('Response from the master accepted. Stopping.')

            print('-' * 80)
            print(any_binary(payload))
            print('-' * 80)

            self.factory.reactor.stop()
        else:
            self.log.error("Non-binary message: {}".format(payload))

    def onClose(self, wasClean, code, reason):
        self.log.debug("Socket closed: {0}".format(reason))


class SugarClientFactory(WebSocketClientFactory, ClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarConsoleProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.maxDelay = 10  # pylint: disable=C0103

    def clientConnectionFailed(self, connector, reason):
        """
        Client connection failed trigger.

        :param connector: Connection peer
        :param reason: failure reason
        :return: None
        """
        self.log.error('Cannot connect console. Is Master running?')
        self.reactor.stop()
