# coding: utf-8
"""
Test struct objects.
"""
import sugar.utils.structs


class TestStructObjects:
    """
    Test suite for struct objects.
    """
    def test_path_slice_nested_dicts(self):
        """
        Test for slicing a dictionary by path.

        :return:
        """
        data = {
            "a": {
                "b": {
                    "c": {
                        "d": "bingo!"
                    }
                }
            }
        }
        assert sugar.utils.structs.path_slice(data, "a", "b", "c", "d").get("d") == "bingo!"

    def test_path_slice_nested_other_objects(self):
        """
        Test for slicing nested dictionary with arbitrary objects in it.

        :return:
        """
        data = {
            "a": {
                "b": {
                    "c": "bingo!",
                },
                "c": "wrong",
            },
            "b": [1, 2],
        }
        assert sugar.utils.structs.path_slice(data, "a", "b", "c").get("c") == "bingo!"

    def test_path_slice_wrong_path(self):
        """
        Wrong path should not crash but return a None.

        :return:
        """
        data = {
            "a": {
                "b": {
                    "c": "bingo!",
                },
                "c": "wrong",
            },
            "b": [1, 2],
        }
        assert sugar.utils.structs.path_slice(data, "a", "b", "missing") is None
        assert sugar.utils.structs.path_slice(data, "a", "b", "c", "d") is None
        assert sugar.utils.structs.path_slice(data, "b", "c", "d", "e") is None
        assert sugar.utils.structs.path_slice(data, "b", "c") is None
        assert sugar.utils.structs.path_slice(data, "a", "b", "c") is not None
        assert sugar.utils.structs.path_slice(data, "a", "c") is not None
