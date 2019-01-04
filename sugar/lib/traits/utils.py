"""
Traits utils
"""

from __future__ import absolute_import, unicode_literals

import platform
import importlib


def get_trait_func(name):
    """
    Get function trait by platform name.

    :param name: Name of the function
    :return: instance of the function (needs to be still executed)
    """
    return getattr(importlib.import_module("sugar.lib.traits.platforms.{}".format(platform.system().lower())), name)
