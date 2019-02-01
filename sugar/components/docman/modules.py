# coding: utf-8
"""
Modules lister.
"""
from sugar.lib.loader import SugarModuleLoader


class ModuleLister:
    """
    Module lister.
    """
    def __init__(self, *paths):
        self.loader = SugarModuleLoader(*paths)  # Get paths from the master config

    def get_all_module_uris(self):
        """
        Get all available modules URIs.

        :return:
        """
        uris = {
            "runners": sorted(list(self.loader.runners.map().keys())),
            "states": sorted(list(self.loader.states.map().keys())),
            "custom": sorted(list(self.loader.custom.map().keys())),  # Limited documentation
        }

        return uris
