# coding: utf-8
"""
State Compiler.
"""
import typing
from sugar.lib.compiler.objresolv import ObjectResolver
from sugar.lib.compiler.objtree import ObjectTree
from sugar.lib.compiler.objtasks import StateTask


class StateCompiler(object):
    """
    State Compiler class.
    """
    def __init__(self, root: str, environment:str = ObjectResolver.DEFAULT_ENV):
        self._object_resolver = ObjectTree(ObjectResolver(path=root, env=environment))

    @property
    def tree(self) -> dict:
        """
        Return object tree.

        :return:
        """
        return self._object_resolver.tree

    @property
    def tasklist(self) -> typing.Tuple[StateTask]:
        """
        Return state tasks sequence.

        Their concurrency should be decided
        by the task performer code.

        :return:
        """
        return (StateTask(), )
