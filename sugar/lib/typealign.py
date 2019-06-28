# coding: utf-8
"""
Type aligner is aligns arguments types to the functions by looking into function definition of the module.
This happens on client, as master normally not supposed to have modules installed.

Flow Description
================

Arguments are pre-parsed syntactically on master. For example, "foo" and "foo,bar" are string and list respectively.
So the argument "something=here" will be translated to a dictionary: {"something": "here"} and following the above
example "something=here,there" will be translated to {"something": ["here", "there"]}. However, in some situations
module expects a list of at least one element. So we would like to have {"something": ["here"]} instead of the string
element. In this case TypeAlign supposed to look at actual function signature and convert the arguments on fly.
"""

import os
import typing
import sugar.lib.exceptions
import sugar.lib.oyaml
import sugar.utils.files


class Aligner:
    """
    Align arguments, based on the doc type description.
    """
    def __init__(self, doc):
        self.doc = doc

    @staticmethod
    def _convert(argvalue, argtype):
        """
        Convert argvalue to the argtype.

        :param argvalue: original value
        :param argtype: original type
        :return:
        """
        if argtype is None:
            return

        # Convert strings to single-item lists
        if argtype == "list" and type(argvalue) in (str, bytes):
            argvalue = [argvalue, ]
        elif argtype == "tuple" and type(argvalue) in (str, bytes):
            argvalue = (argvalue, )

        return argvalue

    def align(self, args, kwargs) -> typing.Tuple[typing.List[typing.Any], typing.Mapping[str, typing.Any]]:
        """
        Align args and keywords.

        :param args:
        :param kwargs:
        :return:
        """
        aligned_kwargs = {}
        for arg_name in kwargs:
            if arg_name in self.doc:
                aligned_kwargs[arg_name] = self._convert(kwargs[arg_name], self.doc[arg_name].get("type"))

        return args, aligned_kwargs


class TypeAlign:
    """
    Type aligner
    """

    def __init__(self, loader):
        self.loader = loader

    @staticmethod
    def _split_uri(uri: str) -> typing.Tuple[str, str]:
        """
        Get URI splitted to the subpath of a module and a function name.

        :param uri:
        :return:
        """
        xuri = uri.split(".")
        assert len(xuri) > 1, "Wrong lenth of the URI: should be at least module in the common namespace and a function"

        return os.path.join(*xuri[:-1]), xuri[-1]

    def _get_function_doc(self, root_path, uri):
        """
        Get function docpath

        :param function_name:
        :param docpath:
        :return:
        """
        subpath, function_name = self._split_uri(uri=uri)
        docpath=os.path.join(root_path, subpath, "doc.yaml")
        if not os.path.exists(docpath):
            raise sugar.lib.exceptions.SugarModuleException("No documentation found for module {}".format(uri))

        with sugar.utils.files.fopen(docpath) as docfh:
            doc = sugar.lib.oyaml.load(docfh).get("tasks", {}).get(function_name, {}).get("parameters")

        assert bool(doc) and doc is not None, "No idea how to run '{}' function. Please fix 'doc.yaml'!".format(uri)

        return doc

    def lookup_runner_function(self, uri):
        """
        Lookup runner function.

        :param uri:
        :return:
        """
        return Aligner(self._get_function_doc(root_path=self.loader.runners.root_path, uri=uri))

    def lookup_state_function(self, uri):
        """
        Lookup state function.

        :param uri:
        :return:
        """
        return Aligner(self._get_function_doc(root_path=self.loader.states.root_path, uri=uri))
