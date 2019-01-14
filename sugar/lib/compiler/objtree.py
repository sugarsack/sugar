"""
Object tree.

Part of the state compiler that allows objects
to be extended, included and inherited.

Object tree does the following:

- Detects circular includes
- Allows inheritance from the other objects
- Allows inclusion/exclusion of objects
- Calls renderers
"""

import collections
from sugar.lib.compat import yaml
import sugar.utils.files
from sugar.lib.compiler.objresolv import ObjectResolver


class ObjectTree:
    """
    Object tree is to take care of sub-files inclusion
    into the main tree. Each sub-state should be first
    rendered with its usual render, so it will return
    already the final dataset, which is going to be
    merged.
    """
    def __init__(self, resolver):
        self._resolver = resolver
        self._dsl_tree = collections.OrderedDict()
        self._uri_stack = {}

    def _resolve_uri(self, uri):
        """
        Resolve URI
        :param uri:
        :return:
        """
        path = self._uri_stack.get(uri)
        if path is None:
            path = self._uri_stack.setdefault(uri, self._resolver.resolve(uri=uri))

        return path

    def _render_statefile(self, uri):
        """
        Render a state file.

        :param uri: State file URI for the resolver
        :return: Rendered YAML structure
        """
        # TODO: add an exception handling if this is failing, so we know which file/subfile is it.
        # TODO: perform here rendering prior loading
        with sugar.utils.files.fopen(self._resolve_uri(uri)) as entry_fh:
            st_src = entry_fh.read()

        return st_src

    def _load_subtree(self, uri):
        return yaml.load(self._render_statefile(uri=uri))

    def _resolve_tree(self, subtree):
        """
        Resolve all the formula tree into one dataset.

        :param uri: URI to resolve
        :return:
        """
        if not isinstance(subtree, collections.Mapping):
            raise Exception("Not a subtree")

        n_tree = collections.OrderedDict()
        for key, val in subtree.items():
            if key == "import":
                for imp_uri in val:  # Imports are usually only few
                    inner = self._load_subtree(imp_uri)
                    for inn_key, inn_val in inner.items():
                        n_tree[inn_key] = inn_val
                    del inner
                n_tree = self._resolve_tree(subtree=n_tree)
            else:
                n_tree[key] = val
        subtree = n_tree
        del n_tree

        return subtree

    def load(self, uri=None):
        """
        Resolve the entry point of the formula.

        :param uri:
        :return:
        """
        self._dsl_tree = self._resolve_tree(self._load_subtree(uri))
