"""
Transport protocol
"""
from __future__ import absolute_import, unicode_literals

from sugar.lib.schemelib import Schema, Use, And, Optional
from sugar.transport.serialisable import Serialisable, ObjectGate


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
    scheme = Schema({
        And('tgt'): str,
        And('fun'): str,
        And('arg'): [],
        And('usr'): str,
        And('jid'): str,
        And('knd'): str,
    })

    @staticmethod
    def create():
        """
        Create message.

        :return:
        """
        return Serialisable()

    @staticmethod
    def validate(obj):
        """
        Validate object.

        :param obj:
        :return:
        """
        ConsoleMsgFactory.scheme.validate(ConsoleMsgFactory.serialise(obj))

    @staticmethod
    def serialise(obj):
        """
        Serialise object.

        :param obj:
        :return:
        """
        return ObjectGate(obj).pack()


class Client(object):
    """
    Client messages
    """


class Server(object):
    """
    Server messages
    """
    response = {
        'msg': [
            {
                's': ErrorLevel.SUCCESS,
                'i': ErrorLevel.INFO,
                'w': ErrorLevel.WARNING,
                'e': ErrorLevel.ERROR
            }
        ]
    }
