# coding: utf-8
"""
Module loader for custom objects.
"""


class CustomModuleLoader:
    """
    Custom user modules. They are very simple functions,
    just like Ansible or Salt modules.

    Custom modules can be both simple and virtual,
    if they are multi-platform implemented.

    """
    def __init__(self, *paths):
        self.paths = paths
        # Here for each path should be VirtualModuleLoader and SimpleModuleLoader
