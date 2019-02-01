# coding: utf-8
"""
Documentation manager and manuals.
"""
import os
import sys
import sugar.lib.exceptions
import sugar.components.docman.gendoc
import sugar.utils.path

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.outputters.console import ConsoleMessages, MappingOutput, TitleOutput, otty
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
        self.gendoc = sugar.components.docman.gendoc.DocMaker()

        self.map_output = MappingOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        self.title_output = TitleOutput(colors=self.config.terminal.colors, encoding=self.config.terminal.encoding)
        self.title_output.add("Available modules")

    def run(self):
        """
        Run documentation manager
        :return:
        """
        if self.args.uri is None:
            otty.puts(self.title_output.paint("Available modules"))
            all_uris = self.modlister.get_all_module_uris()
            for section in sorted(all_uris):
                otty.puts(self.map_output.paint({section: all_uris[section]}, offset="  "))

        loader = self.modlister.get_module_loader(self.args.uri)
        if loader is not None:
            otty.puts(self.gendoc.get_mod_man(self.args.uri))

        if loader is None:
            loader = self.modlister.get_function_loader(self.args.uri)
            if loader is not None:
                otty.puts(self.gendoc.get_func_man(self.args.uri))

        if loader is None:
            raise Exception("No module or function has been found for '{}'.".format(self.args.uri))
