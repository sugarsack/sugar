# coding: utf-8
"""
Main app file, processing CLI
"""

import argparse
import inspect
import sys

from sugar.config import CurrentConfiguration
from sugar.lib.logger import Logger
from sugar.lib import schemelib
from sugar.lib.i18n import gettext as __
from sugar.lib.outputters.console import otty
try:
    import sugarui
except ImportError:
    sugarui = None


class CapitalisedHelpFormatter(argparse.HelpFormatter):
    """
    Custom argparse formatter.
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        """
        On add usage action.

        :param usage: Usage object
        :param actions: List of current actions
        :param groups: Available groups
        :param prefix: Action prefix
        :return: Return the result of HelpFormtter.add_usage
        """
        for action in actions:
            if isinstance(action, argparse._HelpAction):  # pylint: disable=W0212
                action.help = __(action.help)
        return super(CapitalisedHelpFormatter, self).add_usage(usage, actions, groups, prefix)


class SugarCLI(object):
    """
    CLI for running Sugar components in Git style command line interface.
    """
    COMPONENTS = ['master', 'client', 'local', 'keys', 'doc', "ui"]

    def __init__(self):
        parser = argparse.ArgumentParser(
            description=__("Sugar allows for commands to be executed across a space of remote systems in parallel, "
                           "so they can be both controlled and queried with ease."),
            usage=__("""sugar [<target>] [<component>] [<args>]

Target is a name or a pattern in Unix shell-style
wildcard that matches client names.

Available components:

    master     Used to control Sugar Clients
    client     Receives commands from a remote Sugar Master
      keys     Used to manage Sugar authentication keys
     local     Local orchestration

Other:
       doc     Built-in documentation, manuals
        ui     Terminal user interface

"""), formatter_class=CapitalisedHelpFormatter)
        parser.add_argument('component', help=__("Component to run"))
        args = parser.parse_args(sys.argv[1:2])
        if SugarCLI.is_target(args.component):
            self.console()
            sys.exit(1)

        if args.component not in self.COMPONENTS:
            otty.i18n.puts("Unrecognized command")
            parser.print_help()
            sys.exit(1)

        self.log = None
        self.component_cli_parser = None  # Argparse for the current component
        self.component_args = None        # Parsed argparse for the current component

        getattr(self, args.component)()

    @staticmethod
    def is_target(command: str) -> bool:
        """
        Checks if the command is a target.

        :param command: a command from the CLI
        :return: boolean
        """
        ret = False
        for char in ['*', '.', ':']:
            if char in command:
                ret = True
                break

        return ret if ret else command not in SugarCLI.COMPONENTS

    @staticmethod
    def add_common_params(parser: argparse.ArgumentParser):
        """
        Add common CLI params.

        :param parser: argparse.ArgumentParser
        :return: None
        """
        parser.add_argument('-l', '--log-level', help=__("Set output log level. Default: info"),
                            choices=list(sorted(Logger.LOG_LEVELS.keys())), default=None)
        parser.add_argument('-L', '--log-output', help=__("Set destination of the logging. Default: as configured"),
                            default=None)
        parser.add_argument('-c', '--config-dir', help=__("Alternative to default configuration directory"),
                            default=None)

    def setup(self):
        """
        Setup component.

        :raises SchemaError: when configuration validation fails
        :return: None
        """
        self.component_args = self.component_cli_parser.parse_args(sys.argv[2:])
        try:
            conf = CurrentConfiguration(self.component_args.config_dir, self.component_args)
        except schemelib.SchemaError as ex:
            otty.puts("{msg}:\n  {err}".format(msg=__("Configuration error"), err=ex))
            if self.component_args.log_level == 'debug':
                raise ex
            sys.exit(1)
        if self.component_args.log_output is not None:
            conf.update({"log": [{"file": self.component_args.log_output,
                                  "max_size_mb": conf.root.log[0].max_size_mb,
                                  "level": conf.root.log[0].level,
                                  "rotate": conf.root.log[0].rotate}]})

        # This calls configuration! Should be called therefore after singleton init above.
        from sugar.lib.logger.manager import get_logger
        self.log = get_logger(__name__)

    def run(self, reactor):
        """
        Run reactor.

        :param reactor: Twisted reactor
        :raises Exception: raised when log level is "debug" from the CLI
        :return: None
        """
        try:
            if inspect.isclass(type(reactor)) and not type(reactor) == type:  # pylint: disable=C0123
                reactor.run()
            else:
                reactor(self.component_args).run()
        except Exception as ex:
            sys.stderr.write('{errmsg} {msg}:\n  {err}\n'.format(errmsg="Error running",
                                                                 msg=__(sys.argv[1].title()), err=ex))
            if self.component_args.log_level == 'debug':
                raise ex

    def master(self):
        """
        Sugar Master starter.

        :return: None
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description=__("Sugar Master, used to control Sugar Clients"),
            formatter_class=CapitalisedHelpFormatter)

        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.info('Starting Master')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.components.server import SugarServer
        self.run(SugarServer())

    def client(self):
        """
        Sugar Client starter.

        :return: None
        """

        self.component_cli_parser = argparse.ArgumentParser(
            description=__("Sugar Client, receives commands from a remote Sugar Master"),
            formatter_class=CapitalisedHelpFormatter)
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.info('Starting Client')

        # Import order is very important here, since configuration
        # should be read before. Otherwise logging will be initialised
        # before default configuration is adjusted

        from sugar.components.client import SugarClient
        self.run(SugarClient())

    def console(self):
        """
        Sugar console.
        Connects to the locally running master.

        :return: None
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description=__("Sugar Console, sends commants to a remote Sugar Master"),
            formatter_class=CapitalisedHelpFormatter)
        self.component_cli_parser.add_argument('query', nargs="+", help=__("Query"))
        self.component_cli_parser.add_argument('-f', "--offline", action="store_true", help="Include offline clients")
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.debug('Calling Console')

        from sugar.components.console import SugarConsole
        self.run(SugarConsole(self.component_args))

    def keys(self):
        """
        Sugar key manager.
        Used to manage keys of the clients.

        :return: None
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description=__("Sugar Keys Manager, manages authentication keys"),
            formatter_class=CapitalisedHelpFormatter)
        self.component_cli_parser.add_argument("command", help=__("Action on known keys"), default=None,
                                               choices=sorted(["accept", "deny", "reject", "list", "delete"]))
        self.component_cli_parser.add_argument("-f", "--format", help=__("Format of the listing. Default: short"),
                                               default="short", choices=sorted(["short", "full"]))
        self.component_cli_parser.add_argument("-s", "--status", help=__("List only with the following status. "
                                                                         "Default: all"),
                                               default="all", choices=sorted(["all", "new", "accepted",
                                                                              "rejected", "denied"]))
        self.component_cli_parser.add_argument("-t", "--fingerprint",
                                               help=__("Specify key fingerprint of the key"),
                                               default=None)
        self.component_cli_parser.add_argument("-n", "--hostname",
                                               help=__("Specify hostname of the key"),
                                               default=None)
        self.component_cli_parser.add_argument("-i", "--machineid",
                                               help=__("Specify machine ID of the key"),
                                               default=None)
        self.component_cli_parser.add_argument("--match-all-keys-at-once",
                                               help=__("Take all keys for acceptance/rejection/deletion"),
                                               action="store_true")
        SugarCLI.add_common_params(self.component_cli_parser)

        self.setup()
        self.log.debug('Running key manager')

        from sugar.components.keymanager import SugarKeyManager
        self.run(SugarKeyManager)

    def local(self):
        """
        Sugar local caller (orchestration)

        :return: None
        """

    @staticmethod
    def ui():  # pylint: disable=C0103
        """
        Sugar UI (terminal).

        :return: None
        """
        if sugarui is None:
            sys.stderr.write('{errmsg} {msg}:\n  {err}\n'.format(
                errmsg="Error running", msg=__(sys.argv[1].title()), err="UI module was not loaded."))
        else:
            from sugarui import SugarUI
            SugarUI().run()

    def doc(self):
        """
        Documentation render application.

        :return: None
        """
        self.component_cli_parser = argparse.ArgumentParser(
            description=__("Sugar Module Documentation, displays usage and manuals of the modules"),
            formatter_class=CapitalisedHelpFormatter)
        self.component_cli_parser.add_argument("uri", nargs="?",
                                               help=__("URI to the module or module and function. "
                                                       "Leave empty to see all available modules."), default=None,
                                               metavar="module[.function]")
        self.component_cli_parser.add_argument("-t", "--type", choices=["runner", "state", "custom"],
                                               help=__("Search anything in the documentation"), default=None)
        self.component_cli_parser.add_argument("-s", "--search",
                                               help=__("Search anything in the documentation"), default=None)
        SugarCLI.add_common_params(self.component_cli_parser)
        self.setup()
        from sugar.components.docman import DocumentationManager
        self.run(DocumentationManager)
