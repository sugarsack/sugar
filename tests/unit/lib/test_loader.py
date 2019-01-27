# coding: utf-8
"""
Lazy loader unit tests
"""
from sugar.lib.loader import SugarModuleLoader


class TestSugarModuleLoader:
    """
    Sugar module loader test case.
    """
    def test_systemtest_ping(self):
        """
        Test system.test ping module.
        :return:
        """
        sml = SugarModuleLoader()
        out = sml.runners.system.test.ping()
        assert isinstance(out, dict)
        assert "text" in out
        assert out["text"] == "pong"

        out = sml.runners.system.test.ping(text="Hello, world!")
        assert isinstance(out, dict)
        assert "text" in out
        assert out["text"] == "Hello, world!"

        out = sml.states.system.test.pinged(None)
        for section in ["changes", "result", "comment"]:
            assert section in out
        assert out["comment"] == "Success"
        assert "text" in out["result"]
        assert out == sml.states["system.test.pinged"](None)
