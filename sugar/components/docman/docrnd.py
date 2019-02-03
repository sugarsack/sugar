# coding: utf-8
"""
Document render.
"""
import os
import abc
import jinja2

import sugar.utils.files
from sugar.lib.compat import yaml


class ModDocBase(abc.ABC):
    """
    Module documentation base class.
    """
    DOC = "doc.yaml"
    EXAMPLES = "examples.yaml"
    SCHEME = "scheme.yaml"

    def __init__(self, uri, mod_path, *functions):
        """
        Constructor.

        :param mod_path: Module physical path
        :param functions: List of functions to include (others will be removed).
        """
        self._mod_uri = uri
        self._mod_path = mod_path
        self._functions = functions
        self._docmap = {}

        for section in [self.DOC, self.EXAMPLES, self.SCHEME]:
            with sugar.utils.files.fopen(os.path.join(self._mod_path, section), 'r') as dfh:
                self._docmap[section.split(".")[0]] = yaml.load(dfh.read())

    @abc.abstractmethod
    def to_doc(self) -> str:
        """
        Documentation result.

        :return: processible string
        """

    @abc.abstractmethod
    def get_function_manual(self, f_name: str) -> str:
        """
        Generate function documentation.

        :param f_name: Function name
        :return: rendered string
        """
