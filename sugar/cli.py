"""
Main app file, processing CLI
"""

import argparse
import sys
from sugar.client import SugarClient
from sugar.server import SugarServer


class SugarCLI(object):
    """
    CLI for running Sugar components in Git style command line interface.
    """
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
            print('Not implemented yet')
            sys.exit(1)

        if args.component not in ['master', 'client', 'local']:
            print('Unrecognized command')
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
        parser.add_argument('-l', '--log-level', help='Log level',
                            choices=['info', 'error', 'warning', 'debug'])

    def master(self):
        """
        Sugar Master starter.
        :return:
        """
        parser = argparse.ArgumentParser(description='Sugar Master, used to control Sugar Clients')
        SugarCLI.add_common_params(parser)

        args = parser.parse_args(sys.argv[2:])
        server = SugarServer()
        server.run()

    def client(self):
        """
        Sugar Client starter.
        :return:
        """
        parser = argparse.ArgumentParser(description='Sugar Client, receives commands from a remote Sugar Master')
        SugarCLI.add_common_params(parser)

        args = parser.parse_args(sys.argv[2:])
        client = SugarClient()
        client.run()

    def local(self):
        """
        Sugar local caller (orchestration)
        :return:
        """
