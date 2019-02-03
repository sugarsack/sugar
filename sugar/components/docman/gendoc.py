# config: utf-8
"""
Display or generate the documentation for the given module or function.
"""
import os
import colored
import jinja2
from textwrap import wrap
from terminaltables import SingleTable

from sugar.lib.loader import SugarModuleLoader
from sugar.components.docman.docrnd import ModDocBase
from sugar.components.docman import templates


class JinjaCLIFilters:
    @staticmethod
    def req(data):
        """
        Required.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(9), d=data, r=colored.attr("reset"))

    @staticmethod
    def opt(data):
        """
        Optional.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(12), d=data, r=colored.attr("reset"))

    @staticmethod
    def bold(data):
        """
        CLI bold (highlight text)

        :param data:
        :return:
        """
        return "{b}{d}{r}".format(b=colored.attr("bold"), d=data, r=colored.attr("reset"))

    @staticmethod
    def marked(data):
        """
        CLI make marked test.

        :param data:
        :return:
        """
        return "{bg} {b}{fg}{d} {r}".format(bg=colored.bg(8), fg=colored.fg(15), b=colored.attr("bold"),
                                            d=data, r=colored.attr("reset"))


class ModCLIDoc(ModDocBase):
    """
    Module documentation
    """

    filters = JinjaCLIFilters()

    def get_function_manual(self, f_name: str) -> str:
        """
        Generate function documentation.

        :param f_name: Name of the function.
        :return:
        """
        class DocData:
            """
            Documentation data.
            """
        table_data = [
            [self.filters.bold("Parameter"), self.filters.bold("Purpose")],
        ]
        table = SingleTable(table_data)
        table.inner_row_border = True
        term_width = table.column_max_width(1) - 7

        for p_name, p_data in self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {}).get("parameters", {}).items():
            p_descr = os.linesep.join(p_data.get("description", ["N/A"]))
            param = [self.filters.marked(p_name), '',
                     "  " + (self.filters.req("required") if p_data.get("required")
                             else self.filters.opt("optional"))]
            for attr in ["default", "type"]:
                if attr in p_data:
                    param.append("  {}: '{}'".format(attr, self.filters.bold(str(p_data.get(attr)))))
            table_data.append([os.linesep.join(param), os.linesep.join(wrap(p_descr, term_width))])

        func_descr = os.linesep.join(wrap(os.linesep.join(
            self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {}).get("description", "N/A")), term_width))

        m_doc = DocData()
        m_doc.m_uri = self._mod_uri
        m_doc.m_summary = self._docmap.get("doc", {}).get("module", {}).get("summary", "N/A")
        m_doc.m_synopsis = self._docmap.get("doc", {}).get("module", {}).get("synopsis", "N/A")
        m_doc.m_version = self._docmap.get("doc", {}).get("module", {}).get("version", "N/A")
        m_doc.m_added_version = self._docmap.get("doc", {}).get("module", {}).get("since_version", "N/A")

        f_doc = DocData()
        f_doc.f_name = self.filters.marked(f_name)
        f_doc.f_description = func_descr
        f_doc.f_table = table.table

        template = templates.get_template("cli_module")

        return jinja2.Template(template).render(m_doc=m_doc, f_doc=f_doc, fmt=self.filters)

    def to_doc(self) -> str:
        """
        Generate console rich text with escape sequences.

        :return: rtx string
        """
        out = []
        for f_name in self._functions:
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
            text = ModCLIDoc(uri, path).to_doc()

        return text

    def get_func_man(self, loader_name, uri) -> str:
        """
        Get function manual.

        :return: ASCII data with escape sequences.
        """

        text = ''
        uri, func = uri.rsplit(".", 1)
        if loader_name == "runner":
            path = os.path.join(self.loader.runners.root_path, os.path.sep.join(uri.split(".")))
            text = ModCLIDoc(uri, path, func).to_doc()

        return text
        # return "Function {} from {}".format(uri, loader_name)
