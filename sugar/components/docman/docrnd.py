# coding: utf-8
"""
Document render.
"""
import os
import abc

import sugar.utils.files
from sugar.lib.compat import yaml
from sugar.lib.exceptions import SugarException


class ModDocBase(abc.ABC):
    """
    Module documentation base class.
    """
    DOC = "doc.yaml"
    EXAMPLES = "examples.yaml"
    SCHEME = "scheme.yaml"

    filters = None

    def __init__(self, uri, mod_path, *functions, mod_type=None):
        """
        Constructor.

        :param mod_path: Module physical path
        :param functions: List of functions to include (others will be removed).
        """
        self._mod_uri = uri
        self._mod_path = mod_path
        self._functions = functions
        self._docmap = {}
        self._mod_type = mod_type

        doc_found = False
        for section in [self.DOC, self.EXAMPLES, self.SCHEME]:
            try:
                with sugar.utils.files.fopen(os.path.join(self._mod_path, section), 'r') as dfh:
                    self._docmap[section.split(".")[0]] = yaml.load(dfh.read())
                    doc_found = True
            except IOError:
                self._docmap[section] = {}
        if not doc_found:
            raise SugarException("No documentation found for {} module '{}'.".format(mod_type, self._mod_uri))

    def to_doc(self) -> str:
        """
        Generate console rich text with escape sequences.

        :return: rtx string
        """
        out = []
        if self._functions:
            for f_name in self._functions:
                out.append(self.get_function_manual(f_name))
        else:
            self.get_module_toc()
            out.append(self.get_module_toc())

        return os.linesep.join(out)

    @staticmethod
    def _add_ident(data: str, ident: str = "  ", nostrip: bool = False) -> str:
        """
        Add ident to the each line.

        :param data: os.linesep containing data
        :param ident: indent in spaces
        :return: str
        """
        out = []
        for line in data.split(os.linesep):
            if not nostrip:
                line = line.strip()
            out.append("{}{}".format(ident, line))

        return os.linesep.join(out)

    def get_object_examples(self, f_name: str) -> (str, str):
        """
        Get object example for the particular function

        :param f_name: the name of the function
        :return: rendered examples schema
        """
        expl = self._docmap.get("examples", {}).get(f_name, {})
        descr = ' '.join(expl.get("description", []))

        return (descr, self.filters.cli(self._add_ident(expl.get("commandline", ""))),
                self.filters.state(self._add_ident(expl.get("states", "N/A"), nostrip=True)))

    @abc.abstractmethod
    def get_function_manual(self, f_name: str) -> str:
        """
        Generate function documentation.

        :param f_name: Function name
        :return: rendered string
        """

    @abc.abstractmethod
    def get_module_toc(self):
        """
        Get TOC of the module.

        :return: rendered string
        """
