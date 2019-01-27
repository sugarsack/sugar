# coding: utf-8
"""
Lazy loader unit tests
"""
import os
import sys
import pytest
from sugar.lib.loader import SugarModuleLoader
from sugar.lib.loader.base import ModuleMap
import tests.integration


@pytest.fixture
def custmods_path():
    """
    Get custom module path.

    :return:
    """
    return os.path.join(os.path.dirname(tests.integration.__file__),
                        "root", "custmods")


@pytest.fixture
def loader_class():
    """
    Reset modulemap singleton.

    :return:
    """
    ModuleMap.__ref__ = None
    return SugarModuleLoader


class TestSugarModuleLoader:
    """
    Sugar module loader test case.
    """
    def test_custom_module_loader(self, custmods_path, loader_class):
        """
        Custom modules.

        :return:
        """
        sml = loader_class(*[custmods_path])
        for out in [sml.custom.example_module.hello("World"),
                    sml.custom["example_module.hello"]("World")]:
            assert "text" in out
            assert out["text"] == "Hello, World"

        for out in [sml.custom.custping.other_example.ping(),
                    sml.custom["custping.other_example.ping"]()]:
            assert "text" in out
            assert out["text"] == "pong"

    def test_systemtest_ping(self, loader_class):
        """
        Test system.test ping module.
        :return:
        """
        sml = loader_class()

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

    def test_lazyloader_preload(self, custmods_path, loader_class):
        """
        Test blacklist of modules that has to be preloaded
        and never lazyloaded.

        :return:
        """
        uri = "system.test"
        sml = loader_class(custmods_path)
        sml.preload(*[uri])

        assert sml.runners.map()[uri] is not None
        assert sml.states.map()[uri] is not None

    def test_virtloader_present_in_virtual_module(self):
        """
        Virtual module should have self.modules and refer to other siblings.

        :return:
        """
        # TODO: this require any other module, which we do not have yet.
        sys.stdout.write("**>>> POSTPONED TEST <<** ")  # Remove this mark after test implemented
