# coding: utf-8
"""
Components
"""
import json


class ResultDict(dict):
    """
    Results dictionary.
    """
    def _is_na(self, value) -> str:
        """
        If value is None, return "N/A".

        :param value:
        :return: string
        """
        return "N/A" if value is None else value

    def __setitem__(self, key, value):
        if not isinstance(value, (tuple, list, dict)):
            value = self._is_na(value)
        super(ResultDict, self).__setitem__(key, value)

    def to_dict(self) -> dict:
        """
        Kill self type, get just pure dictionary.

        :return:
        """
        return json.loads(json.dumps(self))
