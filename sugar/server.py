# coding: utf-8
"""
Sugar Server

"""

from __future__ import unicode_literals, print_function, absolute_import

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File

import txaio
from autobahn.twisted.websocket import WebSocketServerFactory, listenWS
from sugar.proto import SugarServerProtocol, SugarServerFactory

__author__ = "Bo Maryniuk"
__copyright__ = "Copyright 2018, Sugar Project"
__credits__ = []
__license__ = "Apache 2.0"
__version__ = "0.0.1"
__email__ = "bo@maryniuk.net"
__status__ = "Damn Bloody Alpha"


if __name__ == '__main__':
    txaio.start_logging(level='debug')
    contextFactory = ssl.DefaultOpenSSLContextFactory('key.pem', 'certificate.pem')

    factory = SugarServerFactory(u"wss://127.0.0.1:9000")
    factory.protocol = SugarServerProtocol

    listenWS(factory, contextFactory)

    webdir = File(".")
    webdir.contentTypes['.crt'] = 'application/x-x509-ca-cert'
    web = Site(webdir)

    reactor.run()
