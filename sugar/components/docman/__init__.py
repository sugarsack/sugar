# coding: utf-8
"""
Documentation manager and manuals.
"""
import sys
import sugar.lib.exceptions
from textwrap import wrap
from terminaltables import SingleTable

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.outputters.console import ConsoleMessages, MappingOutput, SystemOutput, TitleOutput
from sugar.components.docman.modules import ModuleLister


class DocumentationManager:
    """
    Documentation manager main class.
    """
    def __init__(self, args):
        self.config = get_config()
        if not self.config.config_path:
            raise sugar.lib.exceptions.SugarConfigurationException("Configuration not found")
        self.log = get_logger(self)
        self.cli = ConsoleMessages(colors=self.config.terminal.colors,
                                   encoding=self.config.terminal.encoding)
        self.args = args
        self.modlister = ModuleLister()

        self.map_output = MappingOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        self.title_output = TitleOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        self.title_output.add("Available modules")
        self.out = SystemOutput(sys.stdout)

    def run(self):
        """
        Run documentation manager
        :return:
        """
        if self.args.uri is None:
            self.out.puts(self.title_output.paint("Available modules"))
            all_uris = self.modlister.get_all_module_uris()
            for section in sorted(all_uris):
                self.out.puts(self.map_output.paint({section: all_uris[section]}, offset="  "))

