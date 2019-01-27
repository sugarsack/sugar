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
