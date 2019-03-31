# coding: utf-8

"""
Server protocols
"""

from __future__ import absolute_import, unicode_literals, print_function
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from sugar.transport import ObjectGate, ServerMsgFactory, ClientMsgFactory, KeymanagerMsgFactory, ConsoleMsgFactory
from sugar.utils import exitcodes
from sugar.components.server.core import get_server_core


class SugarConsoleServerProtocol(WebSocketServerProtocol):
    """
    Console protocol for server.
    """
    def onConnect(self, request):
        self.log.debug("console connected: {0}".format(request.peer))

    def onOpen(self):
        self.factory.register(self)
        self.log.debug("console connection has been opened")

    def onMessage(self, payload, binary):
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
        self.factory.unregister(self)
        self.log.debug("console connection has been closed: {0}", reason)

    def connectionLost(self, reason):
        """
        Client connection dies.

        :param reason: connection failure reason
        :return: None
        """
        self.log.debug("console connection has been lost: {0}", reason)
        WebSocketServerProtocol.connectionLost(self, reason)


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

        :param client: client peer
        :return: None
        """
        if client not in self.consoles:
            self.log.debug("registering console: {}".format(client))
            self.consoles.append(client)

    def unregister(self, client):
        """
        Remove control console from the registry.

        :param client: client peer
        :return: None
        """
        if client in self.consoles:
            self.log.debug("unregistering console: {}".format(client))
            self.consoles.remove(client)


class SugarServerProtocol(WebSocketServerProtocol):
    """
    Sugar server protocol.
    """
    def onConnect(self, request):
        self.log.debug("client connected: {0}".format(request.peer))

    def onOpen(self):
        self.factory.register(self)
        self.log.debug("client has opened a connection")

    def onMessage(self, payload, binary):
        if binary:
            msg = ObjectGate().load(payload, binary)
            if self.get_machine_id() is None:
                self.set_machine_id(msg.machine_id)
                self.factory.core.peer_registry.register(machine_id=msg.machine_id, peer=self)

            if msg.kind == ClientMsgFactory.KIND_HANDSHAKE_PKEY_REQ:
                self.log.debug("handshake: public key request")
                self.sendMessage(ObjectGate(self.factory.core.system.on_pub_rsa_request()).pack(binary), binary)

            elif msg.kind == ClientMsgFactory.KIND_HANDSHAKE_TKEN_REQ:
                self.log.debug("handshake: signed token request")
                self.sendMessage(ObjectGate(self.factory.core.system.on_token_request(msg)).pack(binary), binary)

            elif msg.kind == ClientMsgFactory.KIND_HANDSHAKE_PKEY_REG_REQ:
                self.log.debug("handshake: new RSA key registration accepted")
                self.sendMessage(ObjectGate(self.factory.core.system.on_add_new_rsa_key(msg)).pack(binary), binary)

            elif msg.kind == ClientMsgFactory.KIND_TRAITS:
                self.log.debug("Traits update on client connect")
                self.factory.core.refresh_client_pdata(self.machine_id, traits=msg.internal)

            elif msg.kind == ClientMsgFactory.KIND_NFO_RESP:
                answer = msg.internal.get("answer")
                if answer is not None:
                    answer = answer.to_json()
                self.factory.core.jobstore.report_job(jid=msg.jid, hostname=msg.machine_id,
                                                      src=msg.internal.get("src"), log=msg.internal.get("log"),
                                                      answer=answer)
            else:
                self.log.error("CAUTION: unknown message type:", msg.component)

    def onClose(self, wasClean, code, reason):
        self.log.debug("client's connection has been closed: {0}".format(reason))
        self.transport.loseConnection()
        self.factory.unregister(self)
        self.factory.core.remove_client_protocol(self)

    def connectionLost(self, reason):
        """
        Client connection dies.

        :param reason: connection failure reason
        :return: None
        """
        WebSocketServerProtocol.connectionLost(self, reason)

    def get_machine_id(self):
        """
        Get machine ID, if any.

        :return: string of the machine ID or None, if not found.
        """
        return getattr(self, "machine_id", None)

    def set_machine_id(self, machine_id):
        """
        Set machine ID to the connection.

        :param machine_id: Machine ID (string)
        :return: None
        """
        if self.get_machine_id() != machine_id:
            setattr(self, "machine_id", machine_id)


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

        :param client: client peer
        :return: None
        """
        if client not in self.clients:
            self.log.debug("registering a client: {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        """
        Remove client from the registry.

        :param client: client peer
        :return: None
        """
        if client in self.clients:
            self.log.debug("unregistering client: {}".format(client.peer))
            self.clients.remove(client)
