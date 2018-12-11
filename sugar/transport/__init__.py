"""
Transport protocol
"""


class ErrorLevel(object):
    """
    Error level constants
    """
    SUCCESS = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


class Console(object):
    """
    Console messages
    """
    command = {
        'tgt': '*',
        'fun': 'test.ping',
        'arg': [],
        'usr': 'bo',
        'jid': '20181210205756456745',
    }


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
