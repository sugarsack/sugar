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
        assert sugar.utils.structs.path_slice(data, "a", "b", "c", "d") == "bingo!"

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
        assert sugar.utils.structs.path_slice(data, "a", "b", "c") == "bingo!"
