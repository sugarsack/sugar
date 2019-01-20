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
import os
import collections
from sugar.lib.compat import yaml
import sugar.utils.files
import sugar.lib.compiler.objrender
import sugar.lib.exceptions


class TraceRef:
    """
    Reference to the traced object.
    """
    EXC_TRANSLATIONS = {
        "KeyError": "Statement was not found",
    }

    def __init__(self, statement, uri, path, exc):
        self.statement = statement
        self.uri = uri
        self.path = path

        exc_name = exc.__class__.__name__
        self.exception = exc
        self.exception.cause = self.EXC_TRANSLATIONS.get(exc_name, exc_name)


class ExcludesTracker:
    """
    Collector of excludes.
    Serves to track what should be excluded alongside
    in which file statement was added.
    """

    class Ref:
        """
        Exclude ref element.
        """
        def __init__(self, statement, uri, resolver):
            """
            Constructor.
            :param statement: uri to exclude
            :param uri: uri in which statement is
            """
            self.statement = statement
            self._uri = uri
            self._resolver = resolver

        @property
        def uri(self) -> str:
            """
            URI of the file in which reference is

            :return: uri
            """
            return self._uri

        @property
        def path(self) -> str:
            """
            URL of the file in which reference is

            :return: path
            """
            return self._resolver.resolve(self._uri)

    def __init__(self, resolver):
        self._resolver = resolver
        self._collector = []

    def add(self, statement: str, uri: str) -> None:
        """
        Add an exclusion statement.

        :param statement: exclusion statement
        :param uri: uri of the state
        :return: None
        """
        self._collector.append(self.Ref(statement=statement, uri=uri, resolver=self._resolver))

    @property
    def statements(self) -> tuple:
        """
        Exclusion statements with the info for the debugging.

        :return: tuple of references
        """
        return tuple(self._collector)


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
        self._excludes = ExcludesTracker(resolver=self._resolver)
        self._trace = []

    @property
    def tree(self) -> dict:
        """
        Object tree.

        :return: Mapping
        """
        return self._dsl_tree

    def _resolve_uri(self, uri: str) -> str:
        """
        Resolve URI
        :param uri:
        :return: path
        """
        path = self._uri_stack.get(uri)
        if path is None:
            path = self._uri_stack.setdefault(uri, self._resolver.resolve(uri=uri))

        return path

    def _render_statefile(self, uri: str) -> str:
        """
        Render a state file.

        :param uri: State file URI for the resolver
        :return: Rendered YAML structure
        """
        with sugar.utils.files.fopen(self._resolve_uri(uri)) as entry_fh:
            st_src = entry_fh.read()
        try:
            rendered = sugar.lib.compiler.objrender.render(st_src)
        except sugar.lib.exceptions.SugarSCRenderException as exc:
            self._trace.append(TraceRef(statement=None, uri=uri, path=self._resolver.resolve(uri), exc=exc))
            rendered = "{}"

        return rendered

    def _load_subtree(self, uri: str) -> dict:
        """
        Load subtree from the URI.

        :param uri: URI to the substate.
        :return: mapping subtree structure or an empty tree
        """
        return yaml.load(self._render_statefile(uri=uri)) or {}

    def _resolve_tree(self, subtree: dict, uri: str) -> dict:
        """
        Resolve all the formula tree into one dataset.

        :param subtree: subtree to walk around
        :param uri: URI to resolve
        :raises SugarSCResolverException: when state syntax does not represents a tree structure.
        :return: subtree mapping
        """
        if not isinstance(subtree, collections.Mapping):
            raise sugar.lib.exceptions.SugarSCResolverException("State syntax error: not a tree structure.")

        n_tree = collections.OrderedDict()
        for key, val in subtree.items():
            if key == "import":
                for imp_uri in val:  # Imports are usually only few
                    inner = self._load_subtree(imp_uri)
                    for inn_key, inn_val in inner.items():
                        n_tree[inn_key] = inn_val
                    del inner
                n_tree = self._resolve_tree(subtree=n_tree, uri=uri)
            elif key == "exclude":
                for statement in val:
                    self._excludes.add(statement=statement, uri=uri)
            else:
                n_tree[key] = val
        subtree = n_tree
        del n_tree

        return subtree

    def _check_trace(self):
        """
        Iterate of tracepoints, make a message
        error and raise an exception, if any.

        :raises SugarSCException: if trace errors
        :return: None
        """
        msg = []
        for trace in self._trace:
            mpt = ["", "-" * 80]
            if trace.statement is not None:
                mpt.append("Failiing statement: {stm}".format(stm=trace.statement))
            mpt.append("{errname}: {exc}, while calling '{uri}' ({path})".format(
                errname=trace.exception.cause, exc=trace.exception, uri=trace.uri, path=trace.path))
            mpt.append("-" * 80)
            msg.append(os.linesep.join(mpt))
        msg = os.linesep.join(msg)
        if msg:
            raise sugar.lib.exceptions.SugarSCException(msg)

    def load(self, uri: str = None):
        """
        Resolve the entry point of the formula and load the entire [sub]tree.

        :param uri: URI of the resource
        :return: ObjectTree
        """
        self._dsl_tree = self._resolve_tree(self._load_subtree(uri), uri)
        for excluded in self._excludes.statements:
            try:
                del self._dsl_tree[excluded.statement]
            except KeyError as exc:
                self._trace.append(TraceRef(statement=excluded.statement, uri=excluded.uri,
                                            path=excluded.path, exc=exc))
        self._check_trace()

        return self
