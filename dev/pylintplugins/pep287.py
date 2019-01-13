"""
PEP 287: reStructuredText Docstring Format
https://www.python.org/dev/peps/pep-0287/
"""
from __future__ import absolute_import, unicode_literals

import os
import re
import astroid

from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


class PEP287Checker(checkers.BaseChecker):
    """
    Enforce PEP287 reStructuredText docstring format.
    """
    __implements__ = interfaces.IAstroidChecker

    param_keywords = ["return", "returns", "param", "raises"]
    name = "PEP287"
    msgs = {
        "E8010": (
            "'%s' has no return mentioned", "PEP287-no-return",
            "Please document return statement"),
        "E8011": (
            "'%s' has undocumented return statement", "PEP287-no-doc-return",
            "Please specify what return statement is going to return back"),
        "E8012": (
            "Variable arguments are not described in the docstring of '%s'", "PEP287-no-varargs",
            "Please write documentation of the arguments"),
        "E8013": (
            "'%s' has undocumented varargs", "PEP287-no-doc-varargs",
            "Please write documentation for the varargs"),
        "E8014": (
            "Keyword arguments are not mentioned and not described in the docstring of '%s'", "PEP287-no-kwargs",
            "Please describe kwargs what they are for"),
        "E8015": (
            "Parameter '%s' is missing explanation in %s", "PEP287-undocumented-param",
            "Please add a short explanation about this parameter: what it does and/or what accepts"),
        "E8016": (
            "Parameter '%s' is not mentioned in the docstring of %s at all", "PEP287-doc-missing-param",
            "Please document this parameter"),
        "E8017": (
            "Parameter '%s' is mentioned in the docstring, but is not in the function signature ('%s')",
            "PEP287-excessive-param", "Please document this parameter"),
        "E8018": (
            "Docstring of '%s' does not contain main explanation.",
            "PEP287-main-explanation-missing", "Please document this function what it does"),
        "E8019": (
            "One line expected between main explanation and parameters block in '%s'",
            "PEP287-line-after-main-explanation",
            "Before :param or :return one line is needed after the main explanation"),
        "E8020": (
            "Parameters block in '%s' is not the last one",
            "PEP287-params-block-last",
            "Parameters block should be the last one"),
        "E8021": (
            "Docstring in '%s' contains tabs instead of four spaces.",
            "PEP287-tabs",
            "Please do not use tabs, but four spaces instead."),
        "E8022": (
            "Code raises '%s' but the docstring doesn't mention that.",
            "PEP287-raises-missing",
            "Add to the docstring the info about what exceptions are being raised."),
        "E8024": (
            "Code does not raises '%s' as docstring describes.",
            "PEP287-superfluous-raises",
            "Please remove from the docstring superfluous data."),
    }

    def _cleanup_spaces(self, data):
        """
        Remove double- or more spaces into one.

        :param data:
        :return:
        """
        return re.sub(r"\s+", " ", data)

    def _parse_param(self, line):
        """
        Parse one param.

        :param line:
        :return:
        """
        tokens = self._cleanup_spaces(line).split(" ", 2)
        _, arg, doc = tokens + ["" for _ in range(3 - len(tokens))]

        return arg.strip(":"), doc

    def _parse_return(self, line):
        """
        Parse return.

        :param line:
        :return:
        """
        ret = self._cleanup_spaces(line).split(" ", 1)
        return (ret + ['' for _ in range(2 - len(ret))])[-1]

    def _get_doc_params(self, doc):
        """
        Get documentation parameters.

        :param doc:
        :return:
        """
        params = {}
        for line in doc.split(os.linesep):
            line = line.strip()
            if not line:
                continue
            if line.startswith(":param "):
                arg, doc = self._parse_param(line)
                params[arg] = doc
            if line.startswith(":return"):
                params["return"] = self._parse_return(line)

        return params

    def _get_ident_len(self, line):
        """
        Get ident length of the line.

        :param line:
        :return: int
        """
        return len([True for elm in line.split(" ") if not bool(elm)])

    def _check_tabs(self, node):
        """
        There shall be no tabs. Ever.

        :param node: function node
        :return: None
        """
        if len(node.doc.split("\t")) > 1:
            self.add_message("PEP287-tabs", node=node, args=(node.name, ))

    def _check_explanation_block(self, node):
        """
        Docstring should contain explanation block.

        :param node: function node
        :return: None
        """
        docmap = []
        kw_ident = -1
        for idx, line in enumerate(node.doc.rstrip().split(os.linesep)):
            if not idx:
                continue  # Skip newline after triple-quotes
            s_line = line.strip()
            if not s_line:
                docmap.append("-")
            elif s_line.startswith(":") and s_line.split(" ", 1)[0].strip(":") in self.param_keywords:
                docmap.append(":")
                kw_ident = max(self._get_ident_len(line), kw_ident)
            else:
                # a = self._get_ident_len(line)
                docmap.append(":" if kw_ident > -1 and self._get_ident_len(line) > kw_ident else "#")
        docmap = ''.join(docmap)

        if "#:" in docmap or "--:" in docmap:
            self.add_message("PEP287-line-after-main-explanation", node=node, args=(node.name,))

        if "#" not in docmap:
            self.add_message("PEP287-main-explanation-missing", node=node, args=(node.name,))

        if not (docmap.strip(":") + ":").endswith("-:"):
            self.add_message("PEP287-params-block-last", node=node, args=(node.name,))

    def _compare_signature(self, node, d_pars, n_args):
        """
        Find out what is missing.

        :param d_pars: Documentation parameters.
        :param n_args: Node arguments.
        :return:
        """
        signature_names = []
        # Varargs
        if n_args.vararg:
            signature_names.append(n_args.vararg)

        if n_args.vararg and n_args.vararg not in d_pars:
            self.add_message("PEP287-no-varargs", node=node, args=(node.name,))

        # kwarg
        if n_args.kwarg:
            signature_names.append(n_args.kwarg)

        if n_args.kwarg and n_args.kwarg not in d_pars:
            self.add_message("PEP287-no-kwargs", node=node, args=(node.name,))

        # other arguments
        for idx, arg in enumerate(n_args.args):
            signature_names.append(arg.name)
            if idx == 0 and arg.name in ["cls", "self"] or arg.name.startswith("_"):
                continue
            if arg.name not in d_pars:
                self.add_message("PEP287-doc-missing-param", node=node, args=(arg.name, node.name))
            else:
                if not d_pars[arg.name]:
                    self.add_message("PEP287-undocumented-param", node=node, args=(arg.name, node.name,))

        for arg in d_pars:
            if arg not in signature_names and arg not in ["return"]:
                self.add_message("PEP287-excessive-param", node=node, args=(arg, node.name))

        # returns
        if "return" not in d_pars:
            self.add_message("PEP287-no-return", node=node, args=(node.name,))
        elif not d_pars["return"]:
            self.add_message("PEP287-no-doc-return", node=node, args=(node.name,))

    def what_raises(self, node, raises=None):
        """
        Return number of raises statements in the code.

        :param node: function node
        :param raises: Reserved for the internal data transfer
        :return: List of explicitly raised exception class names
        """
        if raises is None:
            raises = []

        for element in node.get_children():
            if isinstance(element, astroid.node_classes.Raise):
                raises.append(element.exc.func.name)
            else:
                raises = self.what_raises(element, raises=raises)

        return raises

    def _check_raises(self, node):
        """
        Find out if a function raises something but
        is not documents that or vice versa.

        :param node: function node
        :return: None
        """
        exceptions = self.what_raises(node)
        for line in node.doc.strip().split(os.linesep):
            line = line.strip()
            if line.startswith(":rais"):
                exc_name = line.replace(":raises ", ":raise ").split(" ", 1)[-1]
                if exc_name not in exceptions:
                    self.add_message("PEP287-superfluous-raises", node=node, args=(exc_name,))
                else:
                    exceptions.pop(exceptions.index(exc_name))
        for exc_name in exceptions:
            self.add_message("PEP287-raises-missing", node=node, args=(exc_name,))

    @utils.check_messages('docstring-triple-quotes')
    def visit_functiondef(self, node):
        """
        Check if docstring always starts and ends from/by triple double-quotes
        and they are on the new line.
        """
        print(">>>", self._check_raises(node))
        if not node.name.startswith("_") and node.doc:
            self._check_tabs(node)
            self._check_explanation_block(node)
            self._compare_signature(node, self._get_doc_params(node.doc), node.args)


def register(linter):
    """
    Required method to auto register this checker
    """
    linter.register_checker(PEP287Checker(linter))
