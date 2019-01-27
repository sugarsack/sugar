# coding: utf-8
"""
Sugar module loader.
Key features:

 - Black-list support. Some things should not be lazy loaded.
 - Load on access demand.
"""

import sugar.modules.runners
import sugar.modules.states

from sugar.lib.loader.simple import SimpleModuleLoader
from sugar.lib.loader.virtual import VirtualModuleLoader
from sugar.lib.loader.custom import CustomModuleLoader
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton


@Singleton
class SugarModuleLoader:
    """
    Sugar module loader.
    """
    def __init__(self, *paths):
        self.log = get_logger(self)
        self.runners = VirtualModuleLoader(entrymod=sugar.modules.runners)
        self.states = SimpleModuleLoader(entrymod=sugar.modules.states, runner_loader=self.runners)
        self.custom = CustomModuleLoader(*paths)

    def preload(self, *uri) -> None:
        """
        URIs to be pre-loaded.

        :param uri: list of uri to be permanently pre-loaded.
        :return: None
        """
        for _uri in uri:
            for loader in [self.runners, self.states, self.custom]:
                try:
                    loader["{}._".format(_uri)]
                except KeyError:
                    pass
                except Exception as ex:
                    self.log.error("Unhandled exception raised while pre-loading module '{}': {}", _uri, str(ex))
