# coding: utf-8

"""
Server protocols
"""

from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from sugar.transport import ObjectGate, ServerMsgFactory, ClientMsgFactory, KeymanagerMsgFactory, ConsoleMsgFactory
from sugar.utils import exitcodes
from sugar.components.server.core import get_server_core
from sugar.utils.tokens import MasterLocalToken


class SugarConsoleServerProtocol(WebSocketServerProtocol):
    """
    Console protocol for server.
    """
    def onConnect(self, request):
        self.log.info("Console connected: {0}".format(request.peer))

    def onOpen(self):
        self.factory.register(self)
        self.log.info("Console WebSocket connection established")

    def onMessage(self, payload, binary):
        local_token = MasterLocalToken().get_token()
        reply = ServerMsgFactory.create_client_msg()
        if binary:
            msg = ObjectGate().load(payload, binary)
            if msg.component == KeymanagerMsgFactory.COMPONENT:
                # Key manager messages
                if not self.factory.core.verify_local_token(msg.token):
                    self.transport.abortConnection()
                else:
                    self.factory.core.keymanager.on_key_status(msg.internal)
            elif msg.component == ConsoleMsgFactory.COMPONENT:
                # Console messages
                self.factory.core.console_request(msg)
                reply.ret.message = "accepted jid: {}".format(msg.jid)
        else:
            reply.ret.message = "Unknown message"
            reply.ret.errcode = exitcodes.EX_GENERIC
        self.sendMessage(ServerMsgFactory.pack(reply), isBinary=True)

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
        self.core = get_server_core()

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

    def onMessage(self, payload, binary):
        if binary:
            msg = ObjectGate().load(payload, binary)
            self.set_machine_id(msg.machine_id)
            if msg.kind == ClientMsgFactory.KIND_HANDSHAKE_PKEY_REQ:
                self.log.info("** Public key request")
                self.sendMessage(ObjectGate(self.factory.core.system.on_pub_rsa_request()).pack(binary), binary)

            elif msg.kind == ClientMsgFactory.KIND_HANDSHAKE_TKEN_REQ:
                self.log.info("** Signed token request")
                self.sendMessage(ObjectGate(self.factory.core.system.on_token_request(msg)).pack(binary), binary)

            elif msg.kind == ClientMsgFactory.KIND_HANDSHAKE_PKEY_REG_REQ:
                self.log.info("New RSA key registration accepted")
                self.sendMessage(ObjectGate(self.factory.core.system.on_add_new_rsa_key(msg)).pack(binary), binary)

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
        self.factory.core.remove_client_protocol(self)

    def get_machine_id(self):
        """
        Get machine ID, if any.

        :return:
        """
        return getattr(self, "machine_id", None)

    def set_machine_id(self, machine_id):
        """
        Set machine ID to the connection.

        :param machine_id:
        :return:
        """
        if self.get_machine_id() != machine_id:
            setattr(self, "machine_id", machine_id)
            self.factory.core.register_client_protocol(self.machine_id, self)


class SugarServerFactory(WebSocketServerFactory):
    """
    Server factory.
    """
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []  # More smarter stuff here to select clients
        self.core = get_server_core()

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
