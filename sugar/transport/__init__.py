"""
Transport protocol
"""
from __future__ import absolute_import, unicode_literals

import os
import pickle
import getpass
from sugar.lib.schemelib import Schema, Use, And, Optional
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


class ConsoleMsgFactory(object):
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

    @staticmethod
    def create():
        """
        Create message.

        :return:
        """
        s = Serialisable()
        s.component = ConsoleMsgFactory.COMPONENT
        s.kind = ConsoleMsgFactory.TASK_REQUEST
        s.user = getpass.getuser()
        s.uid = os.getuid()

        s.target = ''
        s.function = ''
        s.args = []
        s.jid = jidstore.create()

        ConsoleMsgFactory.validate(s)

        return s

    @staticmethod
    def validate(obj):
        """
        Validate object.

        :param obj:
        :return:
        """
        ConsoleMsgFactory.scheme.validate(ConsoleMsgFactory.serialise(obj))

    @staticmethod
    def unpack(obj):
        """
        De-serialise binary object.

        :param obj:
        :return:
        """
        obj = ObjectGate().load(obj, binary=True)
        ConsoleMsgFactory.validate(obj)
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


class ClientMsgFactory(object):
    """
    Client messages
    """
    COMPONENT = 0xF2


class ServerMsgFactory(object):
    """
    Server messages to all components
    """
    COMPONENT = 0xF0

    # kind
    TASK_RESPONSE = 1
    CONSOLE_RESPONSE = 2

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
        }
    })

    @staticmethod
    def create_console_msg():
        """
        Create console message for client
        :return:
        """
        s = ServerMsgFactory().create()
        s.kind = ServerMsgFactory.CONSOLE_RESPONSE
        return s

    @staticmethod
    def create_client_msg():
        """
        Create client message for client
        :return:
        """
        s = ServerMsgFactory().create()
        s.kind = ServerMsgFactory.TASK_RESPONSE
        return s

    def create(self):
        """
        Create arbitrary message.

        :return:
        """
        s = Serialisable()
        s.component = ServerMsgFactory.COMPONENT
        s.kind = 0
        s.user = getpass.getuser()
        s.uid = os.getuid()
        s.jid = jidstore.create()
        s.ret.errcode = exitcodes.EX_OK
        s.ret.message = ''
        s.ret.function = {}

        ServerMsgFactory.validate(s)

        return s

    @staticmethod
    def validate(obj):
        """
        Validate object.

        :param obj:
        :return:
        """
        ServerMsgFactory.scheme.validate(ServerMsgFactory.serialise(obj))

    @staticmethod
    def unpack(obj):
        """
        De-serialise object from binary.

        :param obj:
        :return:
        """
        obj = ObjectGate().load(obj, binary=True)
        ServerMsgFactory.validate(obj)
        return obj

    @staticmethod
    def pack(obj):
        """
        Serialise object into binary

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
