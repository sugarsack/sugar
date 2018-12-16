"""
Main app file, processing CLI
"""

import argparse
import inspect
import sys

from sugar.config import CurrentConfiguration
from sugar.lib.logger import Logger
from sugar.lib import schemelib


class SugarCLI(object):
    """
    CLI for running Sugar components in Git style command line interface.
    """
    COMPONENTS = ['master', 'client', 'local', 'keys']

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Sugar allows for commands to be executed across a space of remote systems in parallel, "
                        "so they can be both controlled and queried with ease.",
            usage="""sugar [<target>] [<component>] [<args>]

Target is a name or a pattern in Unix shell-style
wildcard that matches client names.

Available components:

    master     Used to control Sugar Clients
    client     Receives commands from a remote Sugar Master
    keys       Used to manage Sugar authentication keys
    local      Local orchestration""")
        parser.add_argument('component', help='Component to run')
        args = parser.parse_args(sys.argv[1:2])
        if SugarCLI.is_target(args.component):
            self.console()
            sys.exit(1)

        if args.component not in self.COMPONENTS:
            sys.stderr.write('Unrecognized command\n')
            parser.print_help()
            sys.exit(1)

        self.log = None
        self.component_cli_parser = None  # Argparse for the current component
        self.component_args = None        # Parsed argparse for the current component

        getattr(self, args.component)()

    @staticmethod
    def is_target(command):
        """
        Checks if the command is a target.

        :param command:
        :return:
        """
        for c in ['*', '.', ':']:
            if c in command:
                return True
        return command not in SugarCLI.COMPONENTS

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

    def setup(self):
        """
        Setup component.
        :return:
        """
        self.component_args = self.component_cli_parser.parse_args(sys.argv[2:])
        try:
            CurrentConfiguration(self.component_args.config_dir, self.component_args)
        except schemelib.SchemaError as ex:
            sys.stderr.write('Configuration error:\n  {}\n'.format(ex))
            if self.component_args.log_level == 'debug':
                raise ex
            sys.exit(1)

        # This calls configuration! Should be called therefore after singleton init above.
        from sugar.lib.logger.manager import get_logger

        self.log = get_logger(__name__)

    def run(self, reactor):
        """
        Run reactor.

        :param reactor:
        :return:
        """
        try:
            if inspect.isclass(type(reactor)) and not type(reactor) == type:
                reactor.run()
            else:
                reactor(self.component_args).run()
        except Exception as ex:
            sys.stderr.write('Error running {}:\n  {}\n'.format(sys.argv[1].title(), ex))
            if self.component_args.log_level == 'debug':
                raise ex

    def master(self):
        """
        Sugar Master starter.
        :return:
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description='Sugar Master, used to control Sugar Clients')
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.info('Starting Master')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.server import SugarServer
        self.run(SugarServer())

    def client(self):
        """
        Sugar Client starter.
        :return:
        """

        self.component_cli_parser = argparse.ArgumentParser(
            description='Sugar Client, receives commands from a remote Sugar Master')
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.info('Starting Client')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.client import SugarClient
        self.run(SugarClient())

    def console(self):
        """
        Sugar console.
        Connects to the locally running master.

        :return:
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description='Sugar Console, sends commants to a remote Sugar Master')
        self.component_cli_parser.add_argument('query', nargs="+", help="Query")
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.debug('Calling Console')

        from sugar.console import SugarConsole
        self.run(SugarConsole(self.component_args))

    def keys(self):
        """
        Sugar key manager.
        Used to manage keys of the clients.

        :return:
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description='Sugar Keys Manager, manages authentication keys')
        self.component_cli_parser.add_argument("command", help="Action on known keys", default=None,
                                               choices=sorted(["accept", "deny", "reject", "list"]))
        self.component_cli_parser.add_argument("-f", "--format", help="Format of the listing. Default: short",
                                               default="short", choices=sorted(["short", "full"]))
        self.component_cli_parser.add_argument("-s", "--status", help="List only with the following status. "
                                                                      " Default: all",
                                               default="all", choices=sorted(["all", "accepted", "rejected", "denied"]))
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.debug('Running key manager')

        from sugar.components.keymanager import SugarKeyManager
        self.run(SugarKeyManager)

    def local(self):
        """
        Sugar local caller (orchestration)
        :return:
        """
