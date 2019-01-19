"""
Tests for the main State Compiler object.
"""

import pytest
import sugar.lib.exceptions
from sugar.lib.compiler import StateCompiler
from sugar.lib.compiler.objresolv import ObjectResolver
from tests.integration.lib.test_compiler_tree import get_states_root


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

        :param get_states_root:
        :return:
        """

        with pytest.raises(sugar.lib.exceptions.SugarSCException) as exc:
            get_compiler.tree.get("foo")
        assert "Nothing compiled yet" in str(exc)
