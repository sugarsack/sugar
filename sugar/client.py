"""
Sugar client
"""

import sys
from optparse import OptionParser

from twisted.python import log
from twisted.internet import reactor, ssl
import random

from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from sugar.proto import SugarClientFactory

ID = random.randint(0xf, 0xff)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    parser = OptionParser()
    parser.add_option("-u", "--url", dest="url",
                      help="The WebSocket URL", default="wss://127.0.0.1:9000")
    (options, args) = parser.parse_args()

    factory = SugarClientFactory(options.url)

    if not factory.isSecure:
        raise Exception('Unable to initialte TLS')

    connectWS(factory, ssl.ClientContextFactory())
    reactor.run()
