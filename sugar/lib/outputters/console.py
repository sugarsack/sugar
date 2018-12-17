"""
CLI output formatters.
"""

from __future__ import absolute_import, print_function, unicode_literals

import colored


class _BaseOutput(object):
    """
    Basic output.
    """

    _ident = "   "

    _symbols_ascii = {
        "leaf": "\\__",
        "bullet": "*",
        "list": "-",
    }

    _symbols_utf = {
        "leaf": "\u2514\u2500\u2500\u2510",
        "bullet": chr(0x25a0),
        "list": chr(0x2509),
    }

    _colors_16 = {
        "types": {
            "bool": colored.fg(13),
            "int": colored.fg(12),
            "float": colored.fg(12),
            "str": colored.fg(10)
        },
        "elements": {
            "key": colored.fg(6),
            "leaf": colored.fg(6),
        }
    }

    _colors_256 = {
        "types": {
            "bool": colored.fg(208),
            "int": colored.fg(183),
            "float": colored.fg(183),
            "str": colored.fg(184)
        },
        "elements": {
            "key": colored.fg(35),
            "leaf": colored.fg(35),
        }
    }

    def __init__(self, colors=16, encoding="ascii"):
        self._colors = colors
        self._encoding = encoding

    def _get_color_scheme(self):
        """
        Get color scheme
        :return:
        """
        return getattr(self, "_colors_{}".format(self._colors))

    def _get_symbol_scheme(self):
        """
        Get symbols scheme
        :return:
        """
        return getattr(self, "_symbols_{}".format(self._encoding))

    def c_type(self, value):
        """
        Color type.

        :param value:
        :return:
        """
        return self._get_color_scheme()["types"].get(type(value).__name__, colored.attr("reset"))

    def c_leaf(self, offset):
        """
        Insert leaf.

        :return:
        """
        return "{}{}".format(offset + self._ident, self._get_symbol_scheme()["leaf"])

    def paint(self, obj, offset=""):
        """
        Paint an object on the screen.

        :return:
        """
        raise NotImplementedError("Not implemented")


class MappingOutput(_BaseOutput):
    """
    Output dictionary.
    """
    def c_key(self):
        """
        Color key.
        :return:
        """
        return self._get_color_scheme()["elements"]["key"]

    def paint(self, obj, offset=""):
        """
        Paint mapping output.

        :return:
        """
        out = []
        for key, value in obj.items():
            out.append("{}{}{}{}:".format(offset, self.c_key(), key, colored.attr("reset")))
            if isinstance(value, dict):
                out.append(self.c_leaf(offset))
                out.append(self.paint(value, offset + self._ident))
            elif isinstance(value, (list, tuple)):
                out.append(self.c_leaf(offset))
                out.append(IterableOutput(colors=self._colors,
                                          encoding=self._encoding).paint(value, offset=offset))
            else:
                out.append("{}{}{}{}".format(offset + self._ident, self.c_type(value), value, colored.attr("reset")))
        return '\n'.join(out)


class IterableOutput(_BaseOutput):
    """
    Output iterable (list, tuple)
    """
    def paint(self, obj, offset=""):
        """
        Paint iterable output.
        :return:
        """
        out = []
        for item in obj:
            if isinstance(item, dict):
                out.append(self.c_leaf(offset))
                out.append(MappingOutput(colors=self._colors,
                                         encoding=self._encoding).paint(item, offset=offset + self._ident))
            elif isinstance(item, (list, tuple)):
                out.append(self.c_leaf(offset))
                out.append(self.paint(item, offset + self._ident))
            else:
                out.append("{}{} {}{}{}".format(offset + self._ident, self._get_symbol_scheme()["list"],
                                                self.c_type(item), item, colored.attr("reset")))
        return '\n'.join(out)
