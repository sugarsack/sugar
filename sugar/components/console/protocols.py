# coding: utf-8

"""
Console protocols
"""

from __future__ import absolute_import, unicode_literals, print_function

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ClientFactory

from sugar.transport import ConsoleMsgFactory, ServerMsgFactory
from sugar.components.console.core import ConsoleCore
import sugar.lib.exceptions


class SugarConsoleProtocol(WebSocketClientProtocol):
    """
    Sugar client protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)

    def onConnect(self, response):
        self.log.debug("console connected: {0}".format(response.peer))

    def onOpen(self):
        try:
            msg_obj = self.factory.console.get_task()
            self.sendMessage(ConsoleMsgFactory.pack(msg_obj), isBinary=True)
        except sugar.lib.exceptions.SugarConsoleException as exc:
            self.log.error(str(exc))
            self.factory.reactor.stop()

    def onMessage(self, payload, binary):
        if binary:
            response = ServerMsgFactory.unpack(payload)
            self.log.debug('reply: {}'.format(response.ret.message))
            self.factory.core.display_response(payload)
        else:
            self.log.error("Non-binary message: {}".format(payload))

        self.log.debug('response from the master accepted. Stopping.')
        self.factory.reactor.stop()

    def onClose(self, wasClean, code, reason):
        self.log.debug("socket closed: {0}".format(reason))


class SugarClientFactory(WebSocketClientFactory, ClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarConsoleProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.maxDelay = 10  # pylint: disable=C0103
        self.core = ConsoleCore()

    def clientConnectionFailed(self, connector, reason):
        """
        Client connection failed trigger.

        :param connector: Connection peer
        :param reason: failure reason
        :return: None
        """
        self.log.error('cannot connect with the console. Is Master is running locally?')
        self.reactor.stop()
