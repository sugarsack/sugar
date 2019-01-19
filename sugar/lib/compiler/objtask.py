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


class FunctionObject:
    """
    Function task object.

    An actual task of the State Task object.
    This object carries all the information for
    an exact task to be performed by the client.
    """


class StateTask:
    """
    State task object.

    """
    def __init__(self):
        self._func_obs = []
