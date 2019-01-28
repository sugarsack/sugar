# coding: utf-8
"""
Blah
"""
# pylint:disable=W0613

from sugar.utils.absmod import BaseStateModule


class TestState(BaseStateModule):
    """
    Implementation of system testing.
    """

    def pinged(self, name, *args, **kwargs):
        """
        State module.

        :param name: state ID (unused here)
        :param args: arguments
        :param kwargs: keywords
        :returns: return JSON object
        """
        result = self.modules.system.test.ping("Pong from {}".format(self.traits.data["host"]))
        return self.to_return(result=result)
