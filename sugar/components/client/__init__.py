"""
Sugar client
"""
import signal

from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import connectWS

from sugar.components.client.protocols import SugarClientFactory
from sugar.config import get_config
from sugar.lib.logger.manager import get_logger


class SugarClient(object):
    """
    Sugar client class.
    """

    def __init__(self):
        """
        Init
        """
        self.config = get_config()
        self.log = get_logger(__name__)

        url = None

        # TODO: cluster connect
        for target in self.config.master:
            url = 'wss://{h}:{p}'.format(h=target.hostname, p=target.ctrl_port)
            break

        self.factory = SugarClientFactory(url)
        self.factory.core.system.on_startup()

        if not self.factory.isSecure:
            self.log.error("TLS is not available. Raising an exception.")
            raise Exception('Unable to initialte TLS')

        signal.signal(signal.SIGINT, self.factory.core.system.on_shutdown)

    def run(self):
        """
        Run client.

        :return: None
        """
        self.factory.core.set_reactor_connection(connectWS(self.factory, ssl.ClientContextFactory()))
        reactor.run()  # pylint: disable=E1101
