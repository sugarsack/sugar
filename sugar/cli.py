"""
Main app file, processing CLI
"""

import argparse
import sys

from sugar.config import CurrentConfiguration
from sugar.lib.logger import Logger


class SugarCLI(object):
    """
    CLI for running Sugar components in Git style command line interface.
    """
    COMPONENTS = ['master', 'client', 'local']

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Sugar allows for commands to be executed across a space of remote systems in parallel, "
                        "so they can be both controlled and queried with ease.",
            usage="""sugar [<target>] [<component>] [<args>]

Target is a name or a pattern in Unix shell-style
wildcard that matches client names.

Available components:

    master     Sugar Master, used to control Sugar Clients
    client     Sugar Client, receives commands from a remote Sugar Master
    local      Sugar local orchestration""")
        parser.add_argument('component', help='Component to run')
        args = parser.parse_args(sys.argv[1:2])
        if SugarCLI.is_target(args.component):
            sys.stderr.write('Not implemented yet\n')
            sys.exit(1)

        if args.component not in self.COMPONENTS:
            sys.stderr.write('Unrecognized command\n')
            parser.print_help()
            sys.exit(1)

        getattr(self, args.component)()

    @staticmethod
    def is_target(command):
        """
        Checks if the command is a target.

        :param command:
        :return:
        """
        # See if it matches any of registered clients
        return "*" in command  # TODO: hack-stub

    @staticmethod
    def add_common_params(parser):
        """
        Add common CLI params.

        :param parser:
        :return:
        """
        parser.add_argument('-l', '--log-level', help='Set output log level. Default: info',
                            choices=list(sorted(Logger.LOG_LEVELS.keys())), default=None)
        default = '/etc/sugar'
        parser.add_argument('-c', '--config-dir', help='Alternative to default configuration directory. '
                                                       'Default: {}'.format(default), default=default)

    def setup(self, args):
        """
        Setup component
        :return:
        """
        CurrentConfiguration(args.config_dir, args)

        # This calls configuration! Should be called therefore after singleton init above.
        from sugar.lib.logger.manager import get_logger

        self.log = get_logger(__name__)

    def master(self):
        """
        Sugar Master starter.
        :return:
        """
        parser = argparse.ArgumentParser(description='Sugar Master, used to control Sugar Clients')
        SugarCLI.add_common_params(parser)

        self.setup(parser.parse_args(sys.argv[2:]))
        self.log.info('Starting Master')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.server import SugarServer
        SugarServer().run()

    def client(self):
        """
        Sugar Client starter.
        :return:
        """

        parser = argparse.ArgumentParser(description='Sugar Client, receives commands from a remote Sugar Master')
        SugarCLI.add_common_params(parser)

        self.setup(parser.parse_args(sys.argv[2:]))
        self.log.info('Starting Client')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.client import SugarClient
        SugarClient().run()

    def local(self):
        """
        Sugar local caller (orchestration)
        :return:
        """
