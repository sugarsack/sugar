# coding: utf-8
"""
Testing utilities for the System
"""

from sugar.modules.runners.system.test.interface import SysTestInterface


class SysTestModule(SysTestInterface):
    """
    System test interface
    """
    def ping(self, text: str = "pong") -> str:
        """
        Return a text back to the system on ping.

        :returns: string text
        """
        result = self.new_result()
        result["text"] = text

        return result
