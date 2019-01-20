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


class FunctionObject:
    """
    Function call object.

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
            name=self.__class__.__name__, mem=hex(id(self)), mdl=self.module, fnc=self.function,
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

    @property
    def calls(self) -> tuple:
        """
        Return function calls.

        :return: tuple of function calls
        """
        return tuple(self._func_obs or [])

    @staticmethod
    def _get_arguments(ref: collections.OrderedDict) -> tuple:
        """
        Classify arguments and keywords.

        :param ref: dictionary of the state args body
        :return: tuple (args, kwargs
        """
        args = []
        kwargs = {}
        for arg in ref or {}:
            if isinstance(arg, collections.Mapping):
                kwargs.update(arg)
            else:
                args.append(arg)
        return args, kwargs

    def _add_single_tasks(self) -> None:
        """
        Add a single task instance to the container.

        :param container: a list of the tasks
        :raises SugarSCException: if module does not contain a function.
        :return: None
        """
        func_obj = FunctionObject()

        idn = next(iter(self._state_task))
        _target = next(iter(self._state_task[idn]))
        try:
            func_obj.module, func_obj.function = _target.rsplit(".", 1)
        except (ValueError, TypeError):
            raise sugar.lib.exceptions.SugarSCException(
                "Module should contain function in {}".format(_target))

        func_obj.args, func_obj.kwargs = self._get_arguments(self._state_task[idn][_target])

        if idn.startswith("name:"):
            if "name" in func_obj.kwargs:
                raise sugar.lib.exceptions.SugarSCException("The 'name' cannot be defined both in ID "
                                                            "section and keywords. Statement: {}".format(idn))
            func_obj.args.insert(0, idn.split(":", 1)[-1])
        elif "name" in func_obj.kwargs:
            func_obj.args.insert(0, func_obj.kwargs.pop("name"))
        elif "name" not in func_obj.kwargs and not func_obj.args:
            func_obj.args.append(idn)

        self._func_obs.append(func_obj)

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

        :raises SugarSCException: when task is not single or multiple
        :return: None
        """
        self._func_obs = []
        if self.is_single():
            self._add_single_tasks()
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
