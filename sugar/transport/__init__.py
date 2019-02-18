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
from sugar.utils.tokens import MasterLocalToken
from sugar.utils import exitcodes
from sugar.utils.jid import jidstore
from sugar.lib.traits import Traits


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

        :raises NotImplementedError: if this method is not overridden.
        :return: None
        """
        raise NotImplementedError()

    @classmethod
    def validate(cls, obj):
        """
        Validate object.

        :param obj: Serialisable
        :return: None
        """
        cls.scheme.validate(cls.serialise(obj))

    @classmethod
    def unpack(cls, obj):
        """
        De-serialise binary object.

        :param obj: Serialisable
        :return: None
        """
        obj = ObjectGate().load(obj, binary=True)
        cls.validate(obj)

        return obj

    @staticmethod
    def pack(obj):
        """
        Serialise object into binary.

        :param obj: Serialisable
        :return: binary
        """
        return ObjectGate(obj).pack(binary=True)

    @staticmethod
    def serialise(obj):
        """
        Serialise object into Python dictionary

        :param obj: Serialisable
        :return: JSON
        """
        return ObjectGate(obj).pack()


class KeymanagerMsgFactory(_MessageFactory):
    """
    Key manager messages
    """
    COMPONENT = 0xf4
    TASK_REQUEST = 1

    scheme = Schema({
        Optional('.'): None,  # Marker
        And('component'): int,
        And('kind'): int,
        And('user'): str,
        And('uid'): int,
        And('token'): str,
        And('internal'): str,
    })

    @staticmethod
    def create():
        """
        Create message.

        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = KeymanagerMsgFactory.COMPONENT
        obj.kind = KeymanagerMsgFactory.TASK_REQUEST
        obj.user = getpass.getuser()
        obj.uid = os.getuid()

        obj.token = MasterLocalToken().get_token()
        obj.internal = ''

        KeymanagerMsgFactory.validate(obj)

        return obj


class ConsoleMsgFactory(_MessageFactory):
    """
    Console message
    """
    COMPONENT = 0xf1
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

        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = cls.COMPONENT
        obj.kind = cls.TASK_REQUEST
        obj.user = getpass.getuser()
        obj.uid = os.getuid()

        obj.target = ''
        obj.function = ''
        obj.args = []
        obj.jid = jidstore.create()

        cls.validate(obj)

        return obj


class ClientMsgFactory(_MessageFactory):
    """
    Client messages
    """
    COMPONENT = 0xf2
    KIND_HANDSHAKE_PKEY_REQ = 0xfa      # Public key request
    KIND_HANDSHAKE_TKEN_REQ = 0xfb      # Signed token request
    KIND_HANDSHAKE_PKEY_REG_REQ = 0xfc  # Public key registration request
    KIND_OPR_RESP = 0xa1                # Operational response
    KIND_TRAITS = 0x1                   # Contains traits

    scheme = Schema({
        Optional('.'): None,  # Marker
        And('component'): int,
        And('kind'): int,
        And('user'): str,
        And('uid'): int,
        And('machine_id'): str,

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

        :param kind: int
        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = cls.COMPONENT
        obj.kind = kind
        obj.user = getpass.getuser()
        obj.uid = os.getuid()
        obj.machine_id = Traits().data["machine-id"]

        obj.stdout = ''
        obj.stderr = ''
        obj.messages.success = []
        obj.messages.warning = []
        obj.messages.error = []
        obj.log = []
        obj.changes = {}
        obj.internal = {}

        obj.jid = jidstore.create()

        cls.validate(obj)

        return obj


class ServerMsgFactory(_MessageFactory):
    """
    Server messages to all components
    """
    COMPONENT = 0xf0

    # kind
    TASK_RESPONSE = 1
    CONSOLE_RESPONSE = 2

    KIND_HANDSHAKE_PKEY_RESP = 0xfa              # Public key response
    KIND_HANDSHAKE_TKEN_RESP = 0xfb              # Signed token response
    KIND_HANDSHAKE_PKEY_NOT_FOUND_RESP = 0xfc    # Public key not found. Client should [re]send one.
    KIND_HANDSHAKE_PKEY_STATUS_RESP = 0xfd       # Public key registered as "{status}"

    KIND_OPR_REQ = 0xa1                          # Operational request

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

        :return: Serialisable
        """
        obj = cls().create()
        obj.kind = cls.CONSOLE_RESPONSE
        return obj

    @classmethod
    def create_client_msg(cls):
        """
        Create client message for client

        :return: Serialisable
        """
        obj = cls().create()
        obj.kind = cls.TASK_RESPONSE
        return obj

    def create(self, kind=KIND_OPR_REQ):
        """
        Create arbitrary message.

        :param kind: int
        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = self.COMPONENT
        obj.kind = kind
        obj.user = getpass.getuser()
        obj.uid = os.getuid()
        obj.jid = jidstore.create()
        obj.ret.errcode = exitcodes.EX_OK
        obj.ret.message = ''
        obj.ret.function = {}
        obj.internal = {}

        self.validate(obj)

        return obj


class RunnerModulesMsgFactory(_MessageFactory):
    """
    Return objects for the runner modules.
    """
    COMPONENT = 0x10

    scheme = Schema({
        Optional("."): None,  # Marker
        And('component'): int,
        And("errcode"): int,
        And("payload"): {},
        And("infos"): [],
        And("warnings"): [],
        And("errors"): [],
    })

    @classmethod
    def create(cls):
        """
        Create state modules return message.

        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = cls.COMPONENT
        obj.errcode = 0
        obj.payload = {}
        obj.infos = []
        obj.warnings = []
        obj.errors = []

        cls.validate(obj)

        return obj


class StateModulesMsgFactory(_MessageFactory):
    """
    Return objects for the state modules.
    """
    COMPONENT = 0x11

    scheme = Schema({
        Optional("."): None,  # Marker
        And('component'): int,
        And("errcode"): int,
        And("changes"): {},
        And("infos"): [],
        And("warnings"): [],
        And("errors"): [],
    })

    @classmethod
    def create(cls):
        """
        Create state modules return message.

        :return: Serialisable
        """
        obj = Serialisable()
        obj.component = cls.COMPONENT
        obj.errcode = 0
        obj.changes = {}
        obj.infos = []
        obj.warnings = []
        obj.errors = []

        cls.validate(obj)

        return obj


def any_binary(data):
    """
    Parse any known binary messages, detect where
    they belong to and validate them.

    :param data: binary data
    :return: Serialisable
    """
    if not isinstance(data, six.text_type):
        data = pickle.loads(data)

    return data
