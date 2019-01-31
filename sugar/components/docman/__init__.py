# coding: utf-8
"""
Documentation manager and manuals.
"""

import sugar.lib.exceptions

from sugar.config import get_config
from sugar.lib.logger.manager import get_logger
from sugar.lib.outputters.console import ConsoleMessages


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

    def run(self):
        """
        Run documentation manager
        :return:
        """
        print(self.args)
        self.cli.error("Not implemented *just yet*.")
