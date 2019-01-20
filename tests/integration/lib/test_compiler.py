"""
Tests for the main State Compiler object.
"""

import pytest
import sugar.lib.exceptions
from sugar.lib.compiler import StateCompiler
from sugar.lib.compiler.objresolv import ObjectResolver
from tests.integration.fixtures import get_states_root  # pylint:disable=W0611

# pylint:disable=R0201,W0621

@pytest.fixture
def get_compiler(get_states_root):
    """
    Get state compiler instance.

    :param get_states_root: states root path fixture
    :return: None
    """
    return StateCompiler(root=get_states_root,
                         environment=ObjectResolver.DEFAULT_ENV)


class TestStateCompiler:
    """
    State compiler test case.
    """
    def test_compilation_needed(self, get_compiler):
        """
        Not compiled tree should raise an exception
        for the compilation is still required.

        :param get_compiler: compiler instance fixture
        :return: None
        """

        with pytest.raises(sugar.lib.exceptions.SugarSCException) as exc:
            get_compiler.tree.get("foo")
        assert "Nothing compiled yet" in str(exc)

    def test_cmp_single_by_id(self, get_compiler):
        """
        Test compile single task, that refers task by an ID:

        /etc/hosts:
          file.managed:
            - src: sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.single")
        assert len(get_compiler.tasklist) == 5

        task_by_id = get_compiler.tasklist[0]
        assert len(task_by_id.calls) == 1

        call = task_by_id.calls[0]
        assert call.module == "file"
        assert call.function == "managed"
        assert call.args == ["/etc/hosts"]
        assert call.kwargs == {"src": "sugar://hosts"}

    def test_cmp_single_by_name_keyword(self, get_compiler):
        """
        Test compile single task, that refers task by
        the name keyword:

        update_hosts:
          file.managed:
            - name: /etc/hosts
            - src: sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.single")
        assert len(get_compiler.tasklist) == 5

        task_by_id = get_compiler.tasklist[1]
        assert len(task_by_id.calls) == 1

        call = task_by_id.calls[0]
        assert call.module == "file"
        assert call.function == "managed"
        assert call.args == ["/etc/hosts"]
        assert call.kwargs == {"src": "sugar://hosts"}

    def test_cmp_single_by_positional_args(self, get_compiler):
        """
        Test compile single task, that refers task by
        the positional arguments:

        update_hosts:
          file.managed:
            - /etc/hosts
            - sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.single")
        assert len(get_compiler.tasklist) == 5

        task_by_id = get_compiler.tasklist[2]
        assert len(task_by_id.calls) == 1

        call = task_by_id.calls[0]
        assert call.module == "file"
        assert call.function == "managed"
        assert call.args == ["/etc/hosts", "sugar://hosts"]
        assert call.kwargs == {}

    def test_cmp_single_by_args_kwargs(self, get_compiler):
        """
        Test compile single task, that refers task by the
        positional arguments and keywords:

        update_hosts:
          file.managed:
            - /etc/hosts
            - src: sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.single")
        assert len(get_compiler.tasklist) == 5

        task_by_id = get_compiler.tasklist[3]
        assert len(task_by_id.calls) == 1

        call = task_by_id.calls[0]
        assert call.module == "file"
        assert call.function == "managed"
        assert call.args == ["/etc/hosts"]
        assert call.kwargs == {"src": "sugar://hosts"}

    def test_cmp_single_by_id_name_prefix(self, get_compiler):
        """
        Test compile single task, that refers task by the
        'name:' prefix in the ID:

        name:/etc/hosts:
          file.managed:
            - sugar://hosts
            - user: root

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.single")
        assert len(get_compiler.tasklist) == 5

        task_by_id = get_compiler.tasklist[4]
        assert len(task_by_id.calls) == 1

        call = task_by_id.calls[0]
        assert call.module == "system.io.file"
        assert call.function == "managed"
        assert call.args == ["/etc/hosts", "sugar://hosts"]
        assert call.kwargs == {"user": "root"}

    def test_cmp_multiple_by_id(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by an ID:

        >>> /etc/hosts:
        >>>  - file:
        >>>    - managed:
        >>>        - src: sugar://hosts
        >>>    - line:
        >>>        - remove: foo
        >>>        - add: bar
        >>>  - archive:
        >>>    - zip:

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "system.io.file", "function": "managed",
             "args": ["/etc/hosts"], "kwargs": {"src": "sugar://hosts"}},
            {"module": "system.io.file", "function": "line",
             "args": ["/etc/hosts"], "kwargs": {"remove": "foo", "add": "bar"}},
            {"module": "archive", "function": "zip",
             "args": ["/etc/hosts"], "kwargs": {}},
        )
        for call, test in zip(calls[:3], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]

    def test_cmp_multiple_by_name_keyword(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by
        the name keyword:

        >>> update_hosts:
        >>>   - file:
        >>>     - managed:
        >>>       - name: /etc/hosts
        >>>       - src: sugar://hosts
        >>>     - line:
        >>>       - name: /etc/ssh/ssh_config
        >>>       - remove: foo
        >>>       - add: bar
        >>>   - archive:
        >>>     - zip:
        >>>       - name: /etc/hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "system.io.file", "function": "managed",
             "args": [], "kwargs": {"name": "/etc/hosts", "src": "sugar://hosts"}},
            {"module": "system.io.file", "function": "line",
             "args": [], "kwargs": {"name": "/etc/ssh/ssh_config", "remove": "foo", "add": "bar"}},
            {"module": "archive", "function": "zip",
             "args": [], "kwargs": {"name": "/etc/hosts"}},
        )
        for call, test in zip(calls[3:6], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]

    def test_cmp_multiple_by_positional_args(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by
        the positional arguments:

        >>> update_hosts_1:
        >>>   - file:
        >>>     - managed:
        >>>         - /etc/hosts
        >>>         - sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "file", "function": "managed",
             "args": ["/etc/hosts", "sugar://hosts"], "kwargs": {}},
        )
        for call, test in zip(calls[6:7], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]

    def test_cmp_multiple_by_args_kwargs(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by the
        positional arguments and keywords:

        >>> update_hosts_2:
        >>>   - file:
        >>>     - managed:
        >>>       - /etc/hosts
        >>>       - src: sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "file", "function": "managed",
             "args": ["/etc/hosts"], "kwargs": {"src": "sugar://hosts"}},
        )
        for call, test in zip(calls[7:8], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]

    def test_cmp_multiple_by_id_tagged(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by the "name" tagged id.

        >>> name:/etc/hosts:
        >>>   - file:
        >>>     - managed:
        >>>       - src: sugar://hosts

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "file", "function": "managed",
             "args": ["/etc/hosts"], "kwargs": {"src": "sugar://hosts"}},
        )
        for call, test in zip(calls[8:9], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]

    def test_cmp_multiple_by_id_nothing_specified(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by the id, while nothing is specified:

        >>> /etc/someconfig.conf:
        >>>   - file:
        >>>     - archived:

        :param get_compiler: compiler instance fixture
        :return: None
        """
        get_compiler.compile("tasks.multiple")
        assert get_compiler.tasklist

        calls = []
        for task in get_compiler.tasklist:
            for call in task.calls:
                calls.append(call)
        assert calls

        tests = (
            {"module": "file", "function": "archived",
             "args": ["/etc/someconfig.conf"], "kwargs": {}},
        )
        for call, test in zip(calls[9:10], tests):
            assert call.module == test["module"]
            assert call.function == test["function"]
            assert call.args == test["args"]
            assert call.kwargs == test["kwargs"]
