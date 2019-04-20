# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

import re
import sys

from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import connectWS

from sugar.components.console.protocols import SugarClientFactory
from sugar.transport import ConsoleMsgFactory
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib import six
from sugar.lib.exceptions import SugarConsoleException


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
                key, val = arg.split('=', 1)
                kwargs[key] = self._get_type(val)
        return args, kwargs

    def get_task(self):
        """
        Parse command line command.
        This finds target, function and parameters.

        :raises SugarConsoleException when syntax is not compliant.
        :return: Serialisable
        """
        target = sys.argv[1:2]
        query = self.args.query[::]

        if "state" in sys.argv[2:]:
            query.pop(0)  # Remove 'state' switch
            cnt = ConsoleMsgFactory.create(kind=ConsoleMsgFactory.STATE_REQUEST)
            cnt.target = target[0] if target else ':'
            uri = query.pop(0).strip(":")
            cnt.arg = self._get_args(query)

            if ":" in uri:
                cnt.env, uri = uri.split(":", 1)

            if ":" in uri or "." not in uri:
                raise SugarConsoleException("Invalid URI: {}".format(uri))

            cnt.uri = uri

        elif "orch" in sys.argv[2:]:
            query.pop(0)  # Remove 'orch' switch
            raise SugarConsoleException("Orchestration subsystem is not yet implemented")
        else:
            cnt = ConsoleMsgFactory.create()
            cnt.target = target[0] if target else ':'
            cnt.uri = query.pop(0)
            cnt.arg = self._get_args(query)

            if "." not in cnt.uri:
                raise SugarConsoleException("Target should contain function with the namespace.")

            self.log.debug("query: {}, function: {}, args: {}, offline: {}", cnt.target, cnt.uri, cnt.arg, cnt.offline)

        if self.args.offline:
            cnt.offline = True

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

        self.log = get_logger(self)
        self.log.debug('Socket ')
        self.factory = SugarClientFactory(url)
        self.factory.console = SugarConsoleCore(args)
        if not self.factory.isSecure:
            raise Exception('Unable to initialte TLS')

    def run(self):
        """
        Run client.

        :return: None
        """
        connectWS(self.factory, ssl.ClientContextFactory())
        reactor.run()
