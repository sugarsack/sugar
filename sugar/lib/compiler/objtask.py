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
from sugar.lib.compat import yaml


class FunctionObject:
    """
    Function call object.

    An actual task of the State Task object.
    This object carries all the information for
    an exact task to be performed by the client.
    """
    TYPE_STATE = 0
    TYPE_RUNNER = 1
    TYPE_CUSTOM = 2

    module = None      # Module may include the namespace, e.g. "system.io.file"
    function = None    # Function name to be called from that module
    args = []          # Arguments to the function
    kwargs = []        # Keywords to the function
    type = TYPE_STATE  # Type of the function (state, runner or custom)

    def __repr__(self):
        return "<{name} at {mem} Module: {mdl}, Function: {fnc}, Args: {arg}, Keywords: {kwr}>".format(
            name=self.__class__.__name__, mem=hex(id(self)), mdl=self.module, fnc=self.function,
            arg=self.args, kwr=self.kwargs
        )

    @property
    def src(self) -> str:
        """
        Get source definition of this function.

        :return: string
        """
        data = {
            "function": self.uri,
            "arguments": self.args,
            "keywords": self.kwargs,
        }

        return yaml.dump(data, default_flow_style=False)

    @property
    def uri(self) -> str:
        """
        Get function object call URI.

        :return: string
        """
        return "{m}.{f}".format(m=self.module, f=self.function)


class StateTask:
    """
    State task object.

    """
    def __init__(self, state_task):
        """

        :param state_task:
        """
        assert len(state_task) == 1, "Syntax error: should be one ID only."

        self.idn = None
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

        self.idn = next(iter(self._state_task))
        _target = next(iter(self._state_task[self.idn]))
        try:
            func_obj.module, func_obj.function = _target.rsplit(".", 1)
        except (ValueError, TypeError):
            raise sugar.lib.exceptions.SugarSCException(
                "Module should contain function in {}".format(_target))

        func_obj.args, func_obj.kwargs = self._get_arguments(self._state_task[self.idn][_target])

        if self.idn.startswith("name:"):
            if "name" in func_obj.kwargs:
                raise sugar.lib.exceptions.SugarSCException("The 'name' cannot be defined both in ID "
                                                            "section and keywords. Statement: {}".format(self.idn))
            func_obj.args.insert(0, self.idn.split(":", 1)[-1])
        elif "name" in func_obj.kwargs:
            func_obj.args.insert(0, func_obj.kwargs.pop("name"))
        elif "name" not in func_obj.kwargs and not func_obj.args:
            func_obj.args.append(self.idn)

        self._func_obs.append(func_obj)

    def _add_multiple_tasks(self) -> None:
        """
        Add a multiple tasks instances to the container (batch mode per Task ID).

        :return: None
        """
        self.idn = next(iter(self._state_task))

        # Three nested loops aren't bad here.
        # We expect only one or few items.
        for _target in self._state_task[self.idn]:
            assert len(_target) == 1, "Syntax error: should be only one task per a function call."
            for _module in _target:
                for _task in _target[_module]:
                    func_obj = FunctionObject()
                    func_obj.module = _module
                    assert len(_task) == 1, "Syntax error: should be only one function per a task."
                    func_obj.function = next(iter(_task))
                    func_obj.args, func_obj.kwargs = self._get_arguments(_task[func_obj.function])

                    idn_name = self.idn.split(":", 1)[-1] if self.idn.startswith("name:") else None
                    if "name" not in func_obj.kwargs and idn_name is not None:  # idn is forced to be a name,
                        func_obj.args.insert(0, idn_name)                       # unless overridden.
                    elif "name" not in func_obj.kwargs and not func_obj.args:   # idn is the name
                        func_obj.args.append(self.idn)
                    self._func_obs.append(func_obj)

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
            self._add_multiple_tasks()
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
        return isinstance(self._state_task[next(iter(self._state_task))], objtype) if self._state_task else False
