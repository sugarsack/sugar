"""
CLI output formatters.
"""

from __future__ import absolute_import, print_function, unicode_literals

import colored
import collections


class _BaseOutput(object):
    """
    Basic output.
    """

    _ident = "   "

    _symbols_ascii = {
        "leaf": "\\__",
        "bullet": "*",
        "list": "-",
        "n/a": " <N/A>",
    }

    _symbols_utf = {
        "leaf": "\u2514\u2500\u2500\u2510",
        "bullet": chr(0x25a0),
        "list": chr(0x2509),
        "n/a": " \u25a0N/A\u25a0",
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
            "n/a": colored.fg(7),
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
            "n/a": colored.fg(245),
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

    def c_na(self, offset):
        """
        Insert value or N/A.

        :return:
        """
        return "{}{}{}{}".format(offset + self._ident, self._get_color_scheme()["elements"]["n/a"],
                                 self._get_symbol_scheme()["n/a"], colored.attr("reset"))

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
        if not obj:
            out.append(self.c_na(offset))
        else:
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


class TitleOutput(object):
    """
    Title maker.

    Add as many as needed titles with different colors.
    They will be all equally same width.

    Example:

        t = Title()
        t.add("foo")
        t.add("long one")

    Then "foo" and "long one" will have the same length and style.
    """
    _suffix_ascii = " >>>"
    _suffix_utf = "\u2593\u2592\u2591"

    _styles_16 = {
        "alert": {
            "f": 15,
            "b": 1,
        },

        "warning": {
            "f": 0,
            "b": 3,
        },

        "success": {
            "f": 0,
            "b": 2,
        },

        "info": {
            "f": 15,
            "b": 4,
        }
    }

    _styles_256 = {
        "alert": {
            "f": 226,
            "b": 160,
        },

        "warning": {
            "f": 232,
            "b": 172,
        },

        "success": {
            "f": 232,
            "b": 70,
        },

        "info": {
            "f": 255,
            "b": 63,
        }
    }

    def __init__(self, colors=16, encoding="ascii"):
        self._colors = colors
        self._encoding = encoding
        self._titles = collections.OrderedDict()

    def _get_style(self):
        """
        Get style.

        :return:
        """
        return self.__class__.__dict__.get("_styles_{}".format(self._colors), self._styles_16)

    def _get_suffix(self):
        """
        Get suffix.

        :return:
        """
        return self.__class__.__dict__.get("_suffix_{}".format(self._encoding), self._suffix_ascii)

    def add(self, title, style):
        """
        Add title.

        :param title:
        :param color:
        :return:
        """
        self._titles[title] = style

    def paint(self, text):
        """
        Paint a title.

        :param title:
        :return:
        """
        style = self._titles.get(text)
        if style:
            style = self._get_style()[style]
            title = "{b} {f}{ab}{t} {r}{bf}{s}{r}".format(
                b=colored.bg(style["b"]), f=colored.fg(style["f"]),
                t=text + (" " * (len(max(self._titles)) - len(text))),
                r=colored.attr("reset"), bf=colored.fg(style["b"]),
                ab=colored.attr("bold"), s=self._get_suffix())
        else:
            title = text

        return title
