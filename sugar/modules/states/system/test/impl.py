# coding: utf-8
"""
Blah
"""
from sugar.utils.absmod import BaseStateModule


class TestState(BaseStateModule):
    """
    Implementation of system testing
    """

    def pinged(self, name, *args, **kwargs):
        """
        State module.
        """
        result = self.modules.system.test.ping("Pong from {}".format(self.traits.data["host"]))
        return self.to_return(result=result)
