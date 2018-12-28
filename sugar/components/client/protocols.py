# coding: utf-8
"""
Client protocols
"""
from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import threads

from sugar.components.client.core import ClientCore
from sugar.transport import ObjectGate, ServerMsgFactory, ClientMsgFactory
import sugar.transport.utils
import sugar.utils.stringutils


class SugarClientProtocol(WebSocketClientProtocol):
    """
    Sugar client protocol.
    """
    def __init__(self):
        WebSocketClientProtocol.__init__(self)
        self._id = sugar.transport.utils.gen_id()

    def onConnect(self, response):
        """
        Connection has been made.

        :param response:
        :return:
        """
        self.log.info("Server connected: {0}".format(response.peer))
        self.factory.core.set_protocol(self._id, self)

    def sendMessage(self, payload, is_binary=False, fragment_size=None, sync=False, do_not_compress=False):
        """
        Send message to the peer.

        :param payload:
        :param is_binary:
        :param fragment_size:
        :param sync:
        :param do_not_compress:

        :return:
        """
        if not is_binary:
            payload = sugar.utils.stringutils.to_bytes(payload)
        WebSocketClientProtocol.sendMessage(self, payload=payload, isBinary=is_binary, fragmentSize=fragment_size,
                                            sync=sync, doNotCompress=do_not_compress)

    def onOpen(self):
        """
        Connection opened to the peer.

        :return:
        """
        self.restart_handshake()

    def restart_handshake(self):
        """
        Restarts handshake
        :return:
        """
        self.factory.core.hs.start()

        if not self.factory.core.hs.ended and not self.factory.core.hs.rsa_accept_wait:
            threads.deferToThread(self.factory.core.system.handshake, self)
        elif not self.factory.core.hs.ended and self.factory.core.hs.rsa_accept_wait:
            threads.deferToThread(self.factory.core.system.wait_rsa_acceptance, self)
        elif self.factory.core.hs.ended and not self.factory.core.hs.rsa_accept_wait:
            self.log.debug("Handshake is finished")
        else:
            self.dropConnection()  # Something entirely went wrong

    def onMessage(self, payload, binary):
        """
        Message received from peer.

        :param payload:
        :param is_binary:
        :return:
        """
        if binary:
            msg = ObjectGate().load(payload, binary)
            if msg.kind != ServerMsgFactory.KIND_OPR_REQ:
                self.factory.core.put_message(msg)
        else:
            self.log.debug("non-binary message: {}".format(payload))

    def onClose(self, wasClean, code, reason):
        """
        Connection closed.

        :param wasClean:
        :param code:
        :param reason:
        :return:
        """
        self.log.info("WebSocket connection closed: {0}".format(reason))
        self.factory.core.remove_protocol(self._id)
        self.factory.core.get_queue().queue.clear()
        self.factory.core.hs.reset()


class SugarClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    """
    Factory for reconnection
    """
    protocol = SugarClientProtocol

    def __init__(self, *args, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        ReconnectingClientFactory.__init__(self)
        self.maxDelay = 10
        self.core = ClientCore()

    def clientConnectionFailed(self, connector, reason):
        """
        On clonnection failed.

        :param connector:
        :param reason:
        :return:
        """
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        """
        On connection lost

        :param connector:
        :param reason:
        :return:
        """
        self.resetDelay()
        self.retry(connector)
