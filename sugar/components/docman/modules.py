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

    def get_module_loader(self, uri: str) -> bool:
        """
        Return True if the URI is a module.

        :param uri: URI of the module or a function.
        :return: bool
        """
        loader = None
        for loader_name, uris in self.get_all_module_uris().items():
            if uri in uris:
                loader = getattr(self.loader, loader_name)
                break

        return loader

    def get_function_loader(self, uri: str) -> bool:
        """
        Return True if the URI is a function in the module.

        :param uri: URI of the module or a function.
        :return: bool
        """
        loader = None
        for l_ref in [self.loader.states, self.loader.runners, self.loader.custom]:
            try:
                if bool(l_ref[uri]):
                    loader = l_ref
                    break
            except KeyError:
                pass

        return loader
