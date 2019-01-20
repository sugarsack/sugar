"""
Tests for the main State Compiler object.
"""

import pytest
import sugar.lib.exceptions
from sugar.lib.compiler import StateCompiler
from sugar.lib.compiler.objresolv import ObjectResolver
from tests.integration.fixtures import get_states_root


@pytest.fixture
def get_compiler(get_states_root):
    """
    Get state compiler instance.

    :return:
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

        :param get_barestates_root:
        :return:
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

        :return:
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

        :return:
        """
        assert False

    def test_cmp_single_by_positional_args(self, get_compiler):
        """
        Test compile single task, that refers task by
        the positional arguments:

        update_hosts:
          file.managed:
            - /etc/hosts
            - sugar://hosts

        :return:
        """
        assert False

    def test_cmp_single_by_args_kwargs(self, get_compiler):
        """
        Test compile single task, that refers task by the
        positional arguments and keywords:

        update_hosts:
          file.managed:
            - /etc/hosts
            - src: sugar://hosts

        :return:
        """
        assert False

    def test_cmp_multiple_by_id(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by an ID:

        /etc/hosts:
          - file:
            - managed:
                - src: sugar://hosts
            - line:
                - remove: foo
                - add: bar
          - archive:
            - zip:

        :param get_compiler:
        :return:
        """
        get_compiler.compile("tasks.multiple")

    def test_cmp_multiple_by_name_keyword(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by
        the name keyword:

        update_hosts:
          - file:
            - managed:
              - name: /etc/hosts
              - src: sugar://hosts
            - line:
              - name: /etc/ssh/ssh_config
              - remove: foo
              - add: bar
          - archive:
            - zip:

        :return:
        """
        assert False

    def test_cmp_multiple_by_positional_args(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by
        the positional arguments:

        update_hosts_1:
          - file:
            - managed:
                - /etc/hosts
                - sugar://hosts

        :return:
        """
        assert False

    def test_cmp_multiple_by_args_kwargs(self, get_compiler):
        """
        Test compile multiple tasks, that refers task by the
        positional arguments and keywords:

        update_hosts_2:
          - file:
            - managed:
                - /etc/hosts
                - src: sugar://hosts

        :return:
        """
        assert False
