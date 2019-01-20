# coding: utf-8
"""
State tasks.
Returns a list of validated tasks for the state.

Their concurrent or parallel actions should be
determined by the core that performs them.

State tasks is a list/tuple:
  (
    task1(target1),
    task2(target2),
    task3(target3),
    ...
  )

Each task can have a sequence of its own sub-tasks
over the same target:

  Task(target): [
    function1 <- target,
    function2 <- target,
    function3 <- target,
    ...
  ]
"""

import collections
import sugar.lib.exceptions
from sugar.lib.outputters.console import MappingOutput


class FunctionObject:
    """
    Function task object.

    An actual task of the State Task object.
    This object carries all the information for
    an exact task to be performed by the client.
    """
    module = None    # Module may include the namespace, e.g. "system.io.file"
    function = None  # Function name to be called from that module
    args = []        # Arguments to the function
    kwargs = []      # Keywords to the function

    def __repr__(self):
        return "<{name} at {mem} Module: {mdl}, Function: {fnc}, Args: {arg}, Keywords: {kwr}>".format(
            name=self.__class__.__name__, mem=id(self), mdl=self.module, fnc=self.function,
            arg=self.args, kwr=self.kwargs
        )


class StateTask:
    """
    State task object.

    """
    def __init__(self, state_task):
        """

        :param state_task:
        """
        assert len(state_task) == 1, "Syntax error: should be one ID only."

        self._state_task = state_task
        self._func_obs = None
        self._set_state_tasks()

    def _add_single_task(self, container: list) -> None:
        """
        Add a single task instance to the container.

        :param container: a list of the tasks
        :return: None
        """
        # by id
        # by name
        # by positionals
        # by mixed

    def _add_multiple_tasks(self, container: list) -> None:
        """
        Add a multiple tasks instances to the container.

        :param container: a list of the tasks
        :return: None
        """
        # by id
        # by name
        # by positionals
        # by mixed

    def _set_state_tasks(self) -> None:
        """
        Set top-level state function tasks.
        Each State Task object should have at least one Function Task.

        :return: None
        """
        self._func_obs = []
        if self.is_single():
            self._add_single_task(self._func_obs)
        elif self.is_multiple():
            self._add_multiple_tasks(self._func_obs)
        else:
            raise sugar.lib.exceptions.SugarSCException("Syntax error: task is nor single neither multiple.")

    def is_single(self) -> bool:
        """
        Verify if the task is singular.

        :return: True, if singular.
        """
        return self._complies_to(collections.Mapping)

    def is_multiple(self) -> bool:
        """
        Verify if the task is multiple.

        :return: True, if multiple.
        """
        return self._complies_to(collections.Sequence)

    def _complies_to(self, objtype) -> bool:
        """
        Check if the second level of the task tree
        complies to the passed object type.

        :param objtype: compliant object type
        :return: Returns True if the second level is an instance of the objtype
        """
        ret = False
        for tid in self._state_task.keys():
            ret = isinstance(self._state_task[tid], objtype)
            break

        return ret
