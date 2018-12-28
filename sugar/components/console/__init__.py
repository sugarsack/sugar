# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

import re
import sys

from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import connectWS

from sugar.components.console.protocols import SugarConsoleProtocol, SugarClientFactory
from sugar.transport import ConsoleMsgFactory
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib import six

log = get_logger(__name__)

__author__ = "Bo Maryniuk"
__copyright__ = "Copyright 2018, Sugar Project"
__credits__ = []
__license__ = "Apache 2.0"
__version__ = "0.0.1"
__email__ = "bo@maryniuk.net"
__status__ = "Damn Bloody Alpha"


class SugarConsoleCore(object):
    """
    Sugar console core class.
    """

    def __init__(self, args):
        """
        Constructor.

        :param args:
        """
        self.args = args
        self._r_digits = re.compile(r"\d+")
        self.log = get_logger(self)

    def _get_type(self, val):
        """
        Determine type of the value.

        :param val:
        :return:
        """
        val = six.text_type(val)
        if ',' in val:
            _val = []
            for inner in val.split(","):
                _val.append(self._get_type(inner))
            val = _val[::]
            del _val
        elif val.lower() in ['true', 'false']:
            val = val.lower() == 'true'
        elif self._r_digits.search(val):
            try:
                val = int(val, 16 if val.lower().startswith('0x') else 10)
            except (ValueError, TypeError):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = six.text_type(val)
        else:
            val = six.text_type(val)

        return val

    def _get_args(self, query):
        """
        Get args from the query

        :param query:
        :return:
        """
        args = []
        kwargs = {}
        for arg in query:
            if "=" not in arg:
                args.append(self._get_type(arg))
            else:
                k, v = arg.split('=', 1)
                kwargs[k] = self._get_type(v)
        return args, kwargs

    def get_task(self):
        """
        Parse command line command.
        This finds target, function and parameters.

        :return:
        """
        target = sys.argv[1:2]
        query = self.args.query[::]

        cnt = ConsoleMsgFactory.create()
        cnt.tgt = target and target[0] or ':'
        cnt.fun = query.pop(0)
        cnt.arg = self._get_args(query)

        self.log.debug("Incoming query: {}".format(query))
        self.log.debug("Parsed incoming query: {}".format(cnt.arg))

        return cnt


class SugarConsole(object):
    """
    Sugar console class.
    """

    def __init__(self, args):
        """
        Init
        :param url:
        """
        self.config = get_config()

        url = 'wss://{h}:{p}'.format(h='localhost', p=5507)

        log.debug('Socket ')
        self.factory = SugarClientFactory(url)
        self.factory.console = SugarConsoleCore(args)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def run(self):
        """
        Run client.
        :return:
        """
        connectWS(self.factory, ssl.ClientContextFactory())
        reactor.run()
