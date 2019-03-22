# coding: utf-8
"""
State Compiler.
"""
import typing
from sugar.lib.compiler.objresolv import ObjectResolver
from sugar.lib.compiler.objtree import ObjectTree
from sugar.lib.compiler.objtask import StateTask
import sugar.lib.exceptions
from sugar.lib.compat import yaml


class StateCompiler(object):
    """
    State Compiler class.
    """
    def __init__(self, root: str, environment: str = ObjectResolver.DEFAULT_ENV):
        self._root = root
        self._environment = environment
        self._tasks = self._object_tree = None

    def _get_state_tasks(self) -> list:
        """
        Create state tasks out of the state tree.

        :return: list of tasks
        """
        tasks = []
        for obj_id in self.tree:
            tasks.append(StateTask(state_task={obj_id: self.tree[obj_id]}))

        return tasks

    def compile(self, uri: str) -> 'StateCompiler':  # Will be deprecated in Python 4.0!
        """
        Compile state tree for the given URI.

        :param uri: URI of the state tree
        :return: self
        """
        self._tasks = None
        self._object_tree = ObjectTree(ObjectResolver(path=self._root, env=self._environment))
        self._object_tree.load(uri)

        return self

    @property
    def tree(self) -> dict:
        """
        Return object tree.

        :raises SugarSCException: if tree is not yet compiled
        :return:  dictionary
        """
        if self._object_tree is None:
            raise sugar.lib.exceptions.SugarSCException("Nothing compiled yet")

        return self._object_tree.tree

    @property
    def tasklist(self) -> typing.Tuple[StateTask]:
        """
        Return state tasks sequence.

        Their concurrency should be decided
        by the task performer code.

        :return: tuple of StateTask objects, each contains calls
                 (one for single and many for multiple)
        """
        if self._tasks is None:
            self._tasks = tuple(self._get_state_tasks())

        return self._tasks

    def to_yaml(self) -> str:
        """
        Render YAML source out of the compiled tree.

        :return: YAML source string
        """
        return (yaml.dump(self.tree, default_flow_style=False) or "").strip()
