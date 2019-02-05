# config: utf-8
"""
Display or generate the documentation for the given module or function.
"""
import os
import colored
import jinja2
from textwrap import wrap
from terminaltables import SingleTable

from sugar.lib.exceptions import SugarException
from sugar.lib.loader import SugarModuleLoader
from sugar.components.docman.docrnd import ModDocBase
from sugar.components.docman import templates


class DocData:
    """
    Documentation data.
    """


class JinjaCLIFilters:
    """
    CLI colorisers.
    """

    def state(self, data):
        """
        State code example.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(3), d=data, r=colored.attr("reset"))

    def cli(self, data):
        """
        Command line code example.

        :param data:
        :return:
        """
        return "{f}{d}{r}".format(f=colored.fg(10), d=data, r=colored.attr("reset"))

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

    def _add_ident(self, data, ident="  ", nostrip=False):
        """
        Add ident.

        :param data:
        :param ident:
        :return:
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

        :param f_name:
        :return: rendered examples schema
        """
        expl = self._docmap.get("examples", {}).get(f_name, {})
        descr = ' '.join(expl.get("description", []))

        return (descr, self.filters.cli(self._add_ident(expl.get("commandline", ""))),
                self.filters.state(self._add_ident(expl.get("states", "N/A"), nostrip=True)))

    def get_function_manual(self, f_name: str) -> str:
        """
        Generate function documentation.

        :param f_name: Name of the function.
        :return: rendered manual
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
        m_doc.m_synopsis = self._docmap.get("doc", {}).get("module", {}).get("synopsis", "N/A").strip()
        m_doc.m_version = self._docmap.get("doc", {}).get("module", {}).get("version", "N/A")
        m_doc.m_added_version = self._docmap.get("doc", {}).get("module", {}).get("since_version", "N/A")

        f_doc = DocData()
        f_doc.f_name = self.filters.marked(f_name)
        f_doc.f_description = func_descr.strip()
        f_doc.f_table = table.table if len(table_data) > 1 else None
        f_doc.f_example_descr, f_doc.f_example_cmdline, f_doc.f_example_states = self.get_object_examples(f_name)

        template = templates.get_template("cli_module")

        return jinja2.Template(template).render(m_doc=m_doc, f_doc=f_doc, fmt=self.filters)

    def get_module_toc(self):
        """
        Get TOC of the module.

        :return:
        """
        funcs = self._docmap.get("doc", {}).get("tasks", {})

        table_data = [
            [self.filters.bold("Function"), self.filters.bold("Purpose")],
        ]

        table = SingleTable(table_data)
        table.inner_row_border = True
        term_width = table.column_max_width(1)

        f_last_name = None
        for f_name, f_data in funcs.items():
            f_last_name = f_name
            table_data.append([self.filters.bold(f_name),
                               os.linesep.join(wrap(" ".join(funcs.get(
                                   f_name, {}).get("description", "N/A")), term_width))])

        m_doc = DocData()
        m_doc.m_uri = self._mod_uri
        m_doc.m_summary = self._docmap.get("doc", {}).get("module", {}).get("summary", "N/A")
        m_doc.m_synopsis = self._docmap.get("doc", {}).get("module", {}).get("synopsis", "N/A")
        m_doc.m_version = self._docmap.get("doc", {}).get("module", {}).get("version", "N/A")
        m_doc.m_added_version = self._docmap.get("doc", {}).get("module", {}).get("since_version", "N/A")
        m_doc.m_type = self._mod_type
        m_doc.m_f_name = f_last_name
        m_doc.m_toc = table.table

        template = templates.get_template("cli_mod_toc")
        return jinja2.Template(template).render(m_doc=m_doc, fmt=self.filters)

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
        if loader_name in ["runner", "state"]:
            path = os.path.join(getattr(self.loader, loader_name + "s").root_path, os.path.sep.join(uri.split(".")))
        else:
            raise SugarException("Custom modules documentation is not supported yet.")

        return ModCLIDoc(uri, path, mod_type=loader_name).to_doc()

    def get_func_man(self, loader_name, uri) -> str:
        """
        Get function manual.

        :return: ASCII data with escape sequences.
        """

        text = ''
        uri, func = uri.rsplit(".", 1)
        if loader_name == "runner":
            path = os.path.join(self.loader.runners.root_path, os.path.sep.join(uri.split(".")))
            text = ModCLIDoc(uri, path, func, mod_type=loader_name).to_doc()
        elif loader_name == "state":
            path = os.path.join(self.loader.states.root_path, os.path.sep.join(uri.split(".")))
            text = ModCLIDoc(uri, path, func, mod_type=loader_name).to_doc()

        return text
        # return "Function {} from {}".format(uri, loader_name)
