"""
Transport protocol
"""
from __future__ import absolute_import, unicode_literals

import os
import pickle
import getpass
from sugar.lib.schemelib import Schema, And, Optional
from sugar.lib import six
from sugar.transport.serialisable import Serialisable, ObjectGate
from sugar.utils import exitcodes
from sugar.utils.jid import jidstore


class ErrorLevel(object):
    """
    Error level constants
    """
    SUCCESS = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


class _MessageFactory(object):
    """
    Message.
    """
    scheme = Schema({})

    @classmethod
    def create(cls):
        """
        Create message.

        :return:
        """
        raise NotImplementedError()

    @classmethod
    def validate(cls, obj):
        """
        Validate object.

        :param obj:
        :return:
        """
        cls.scheme.validate(cls.serialise(obj))

    @classmethod
    def unpack(cls, obj):
        """
        De-serialise binary object.

        :param obj:
        :return:
        """
        obj = ObjectGate().load(obj, binary=True)
        cls.validate(obj)

        return obj

    @staticmethod
    def pack(obj):
        """
        Serialise object into binary.

        :param obj:
        :return:
        """
        return ObjectGate(obj).pack(binary=True)

    @staticmethod
    def serialise(obj):
        """
        Serialise object into Python dictionary

        :param obj:
        :return:
        """
        return ObjectGate(obj).pack()


class ConsoleMsgFactory(_MessageFactory):
    """
    Console message
    """
    COMPONENT = 0xF1
    TASK_REQUEST = 1

    scheme = Schema({
        Optional('.'): None,  # Marker
        And('component'): int,
        And('kind'): int,
        And('user'): str,
        And('uid'): int,

        And('target'): str,
        And('function'): str,
        And('args'): [],

        Optional('jid'): str,
    })

    @classmethod
    def create(cls):
        """
        Create message.

        :return:
        """
        s = Serialisable()
        s.component = cls.COMPONENT
        s.kind = cls.TASK_REQUEST
        s.user = getpass.getuser()
        s.uid = os.getuid()

        s.target = ''
        s.function = ''
        s.args = []
        s.jid = jidstore.create()

        cls.validate(s)

        return s


class ClientMsgFactory(_MessageFactory):
    """
    Client messages
    """
    COMPONENT = 0xf2
    KIND_HANDSHAKE_PKEY_REQ = 0xfa  # Public key request
    KIND_HANDSHAKE_TKEN_REQ = 0xfb  # Signed token request
    KIND_OPR_RESP = 0xa1            # Operational response

    scheme = Schema({
        Optional('.'): None,  # Marker
        And('component'): int,
        And('kind'): int,
        And('user'): str,
        And('uid'): int,

        # Channels
        And('stdout'): str,
        And('stderr'): str,
        And('messages'): {
            Optional('.'): None,  # Marker
            And('success'): [],
            And('warning'): [],
            And('error'): [],
        },
        And('log'): [],
        And('changes'): {},
        And('internal'): {},  # Used for non-operational communications (handshake, discovery etc)

        Optional('jid'): str,
    })

    @classmethod
    def create(cls, kind=KIND_OPR_RESP):
        """
        Create message.

        :return:
        """
        s = Serialisable()
        s.component = cls.COMPONENT
        s.kind = kind
        s.user = getpass.getuser()
        s.uid = os.getuid()

        s.stdout = ''
        s.stderr = ''
        s.messages.success = []
        s.messages.warning = []
        s.messages.error = []
        s.log = []
        s.changes = {}
        s.internal = {}

        s.jid = jidstore.create()

        cls.validate(s)

        return s


class ServerMsgFactory(_MessageFactory):
    """
    Server messages to all components
    """
    COMPONENT = 0xf0

    # kind
    TASK_RESPONSE = 1
    CONSOLE_RESPONSE = 2

    KIND_HANDSHAKE_PKEY_RESP = 0xfa  # Public key response
    KIND_HANDSHAKE_TKEN_RESP = 0xfb  # Signed token response
    KIND_OPR_REQ = 0xa1              # Operational request

    scheme = Schema({
        Optional('.'): None,  # Marker
        And('component'): int,
        And('kind'): int,
        And('user'): str,
        And('uid'): int,
        Optional('jid'): str,
        And('ret'): {
            Optional('.'): None,  # Marker
            And('errcode'): int,
            Optional('message'): str,
            Optional('function'): {},
        },
        And('internal'): {},
    })

    @classmethod
    def create_console_msg(cls):
        """
        Create console message for client
        :return:
        """
        s = cls().create()
        s.kind = cls.CONSOLE_RESPONSE
        return s

    @classmethod
    def create_client_msg(cls):
        """
        Create client message for client
        :return:
        """
        s = cls().create()
        s.kind = cls.TASK_RESPONSE
        return s

    def create(self, kind=KIND_OPR_REQ):
        """
        Create arbitrary message.

        :return:
        """
        s = Serialisable()
        s.component = self.COMPONENT
        s.kind = kind
        s.user = getpass.getuser()
        s.uid = os.getuid()
        s.jid = jidstore.create()
        s.ret.errcode = exitcodes.EX_OK
        s.ret.message = ''
        s.ret.function = {}
        s.internal = {}

        self.validate(s)

        return s


def any_binary(data):
    """
    Parse any known binary messages, detect where
    they belong to and validate them.

    :param data:
    :return:
    """
    msg_class = {
        ConsoleMsgFactory.COMPONENT: ConsoleMsgFactory,
        ServerMsgFactory.COMPONENT: ServerMsgFactory,
        ClientMsgFactory.COMPONENT: ClientMsgFactory
    }

    if not isinstance(data, six.text_type):
        data = pickle.loads(data)

    return data
