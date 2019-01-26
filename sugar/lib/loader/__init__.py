# coding: utf-8
"""
Sugar module loader.
Key features:

 - Black-list support. Some things should not be lazy loaded.
 - Load on access demand.
"""

import sugar.modules.runners
import sugar.modules.states
import sugar.utils.absmod

from sugar.lib.loader.simple import SimpleModuleLoader
from sugar.lib.loader.virtual import VirtualModuleLoader
from sugar.lib.loader.custom import CustomModuleLoader


class SugarModuleLoader:
    """
    Sugar module loader.
    """
    def __init__(self, *paths):
        self.runners = VirtualModuleLoader(sugar.modules.runners, filter_type=sugar.utils.absmod.BaseRunnerModule)
        self.states = SimpleModuleLoader(sugar.modules.states, filter_type=sugar.utils.absmod.BaseStateModule)
        self.custom = CustomModuleLoader(*paths)

    def preload(self, *uri) -> None:
        """
        URIs to be pre-loaded.

        :param uri: list of uri to be permanently pre-loaded.
        :return: None
        """
