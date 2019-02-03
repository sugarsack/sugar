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

    def get_all_module_uris(self) -> dict:
        """
        Get all available modules URIs.

        :return: dict of all modules (runners, states, custom).
        """
        uris = {
            "runners": sorted(list(self.loader.runners.map().keys())),
            "states": sorted(list(self.loader.states.map().keys())),
            "custom": sorted(list(self.loader.custom.map().keys())),  # Limited documentation
        }

        return uris

    def is_module(self, uri: str) -> bool:
        """
        Return True if the URI is a module.

        :param uri: URI of the module or a function.
        :return: bool
        """
        ret = False
        for loader_name, uris in self.get_all_module_uris().items():
            if uri in uris:
                ret = True
                break

        return ret

    def is_function(self, uri: str) -> bool:
        """
        Return True if the URI is a function in the module.

        :param uri: URI of the module or a function.
        :return: bool
        """
        ret = False
        for l_ref in [self.loader.states, self.loader.runners, self.loader.custom]:
            try:
                ret = bool(l_ref[uri])
            except KeyError:
                pass
            if ret:
                break

        return ret
