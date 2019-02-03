# config: utf-8
"""
Display or generate the documentation for the given module or function.
"""
import os
import colored
from textwrap import wrap
from terminaltables import SingleTable, AsciiTable

from sugar.lib.loader import SugarModuleLoader
from sugar.components.docman.docrnd import ModDocBase


class ModCLIDoc(ModDocBase):
    """
    Module documentation
    """

    @staticmethod
    def _gen_req(data):
        """
        Required.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(9), d=data, r=colored.attr("reset"))

    @staticmethod
    def _gen_opt(data):
        """
        Optional.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(12), d=data, r=colored.attr("reset"))

    @staticmethod
    def _gen_bld(data):
        """
        CLI bold (highlight text)

        :param data:
        :return:
        """
        return "{b}{f}{d}{r}".format(b=colored.attr("bold"), f=colored.fg(3),
                                     d=data, r=colored.attr("reset"))

    @staticmethod
    def _gen_title(data):
        """
        CLI make title.

        :param data:
        :return:
        """
        return "{bg} {b}{fg}{d} {r}".format(bg=colored.bg(8), fg=colored.fg(15), b=colored.attr("bold"),
                                            d=data, r=colored.attr("reset"))

    def get_function_manual(self, f_name: str) -> str:
        """
        Generate function documentation.

        :param f_name: Name of the function.
        :return:
        """
        table_data = [
            [self._gen_bld("Function"), self._gen_bld("Synopsis")],
            ["{}(...)".format(f_name), ""],
            [self._gen_bld("Parameter"), self._gen_bld("Usage")],
        ]
        table = SingleTable(table_data)
        table.inner_row_border = True
        term_width = table.column_max_width(1) - 7

        table_data[1][1] = os.linesep.join(wrap(os.linesep.join(
            self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {}).get("description", "N/A")), term_width))

        for p_name, p_data in self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {}).get("parameters", {}).items():
            p_descr = os.linesep.join(p_data.get("description", ["N/A"]))
            param = [self._gen_title(p_name), '',
                     "  " + (self._gen_req("required") if p_data.get("required")
                             else self._gen_opt("optional"))]
            for attr in ["default", "type"]:
                if attr in p_data:
                    param.append("  {}: '{}'".format(attr, self._gen_bld(str(p_data.get(attr)))))
            table_data.append([os.linesep.join(param), os.linesep.join(wrap(p_descr, term_width)),])

        return table.table

    def to_doc(self) -> str:
        """
        Generate console rich text with escape sequences.

        :return: rtx string
        """
        out = []
        for f_name in self._docmap.get("doc", {}).get("tasks", {}):
            out.append(self.get_function_manual(f_name))

        return os.linesep.join(out)


class DocMaker:
    """
    Get a particular module or function
    and create a documentation for it.
    """

    def __init__(self):
        self.loader = SugarModuleLoader()

    def get_mod_man(self, loader_name, uri) -> str:
        """
        Get module manual.

        :return: ASCII data with escapes sequences.
        """
        text = ''
        if loader_name == "runner":
            path = os.path.join(self.loader.runners.root_path, os.path.sep.join(uri.split(".")))
            text = ModCLIDoc(path).to_doc()

        return text

    def get_func_man(self, loader_name, uri) -> str:
        """
        Get function manual.

        :return: ASCII data with escape sequences.
        """

        return "Function {} from {}".format(uri, loader_name)
