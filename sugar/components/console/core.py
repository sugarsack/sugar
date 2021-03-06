# coding: utf-8
"""
Console app core
"""

from sugar.utils.objects import Singleton
from sugar.config import get_config
from sugar.lib.outputters import console
from sugar.transport import any_binary


@Singleton
class ConsoleCore:
    """
    Console core.
    """
    def __init__(self):
        self.config = get_config()
        self.console_messages = console.ConsoleMessages(colors=self.config.terminal.colors,
                                                        encoding=self.config.terminal.config)

    def display_response(self, event) -> None:
        """
        Display response message.

        :param event: Response message (binary)
        :return: None
        """
        event = any_binary(event)
        msg_template = event.get("ret", {}).get("msg_template", "")
        msg_args = event.get("ret", {}).get("msg_args", [])
        self.console_messages.info(msg_template, *msg_args)
