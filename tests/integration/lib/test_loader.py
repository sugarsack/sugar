# coding: utf-8
"""
Lazy loader unit tests
"""
import os
import pytest
from sugar.lib.loader import SugarModuleLoader
import tests.integration


@pytest.fixture
def custmods_path():
    return os.path.join(os.path.dirname(tests.integration.__file__),
                        "root", "custmods")


class TestSugarModuleLoader:
    """
    Sugar module loader test case.
    """
    def test_custom_module_loader(self, custmods_path):
        """
        Custom modules.

        :return:
        """
        sml = SugarModuleLoader(*[custmods_path])
        for out in [sml.custom.example_module.hello("World"),
                    sml.custom["example_module.hello"]("World")]:
            assert "text" in out
            assert out["text"] == "Hello, World"

        for out in [sml.custom.custping.other_example.ping(),
                    sml.custom["custping.other_example.ping"]()]:
            assert "text" in out
            assert out["text"] == "pong"

    def test_systemtest_ping(self):
        """
        Test system.test ping module.
        :return:
        """
        sml = SugarModuleLoader()

        for out in [sml.runners.system.test.ping(),
                    sml.runners["system.test.ping"]()]:
            assert isinstance(out, dict)
            assert "text" in out
            assert out["text"] == "pong"

        text = "Darth Wader"
        for out in [sml.runners.system.test.ping(text=text),
                    sml.runners["system.test.ping"](text=text)]:
            assert isinstance(out, dict)
            assert "text" in out
            assert out["text"] == text

        for out in [sml.states.system.test.pinged(None),
                    sml.states["system.test.pinged"](None)]:
            for section in ["changes", "result", "comment"]:
                assert section in out
            assert out["comment"] == "Success"
            assert "text" in out["result"]
            assert out == sml.states["system.test.pinged"](None)
