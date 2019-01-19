"""
Tests for the main State Compiler object.
"""

import pytest
import sugar.lib.exceptions
from sugar.lib.compiler import StateCompiler
from sugar.lib.compiler.objresolv import ObjectResolver
from tests.integration.lib.test_compiler_tree import get_states_root


class TestStateCompiler:
    def test_compilation_needed(self, get_states_root):
        """
        Not compiled tree should raise an exception
        for the compilation is still required.

        :param get_states_root:
        :return:
        """

        scmp = StateCompiler(root=get_states_root, environment=ObjectResolver.DEFAULT_ENV)
        with pytest.raises(sugar.lib.exceptions.SugarSCException) as exc:
            scmp.tree
        assert "Nothing compiled yet" in str(exc)
