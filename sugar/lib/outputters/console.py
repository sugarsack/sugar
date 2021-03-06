"""
CLI output formatters.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import io
import sys
import collections
import colored

from sugar.lib.i18n import gettext as __


class SystemOutput(object):
    """
    replace sys.stdout/stderr for output with i18n.
    """
    def __init__(self, output: io.BytesIO, gtxt=None):
        """
        System outputter.
        :param output: sys.stdout, sys.stderr, string IO, file handler etc
        """
        self.__output = output
        self.gettext = gtxt if gtxt is not None else lambda data: data

    def write(self, data):
        """
        Write data content to the output device.

        :param data: bytes
        :return: None
        """
        self.__output.write(self.gettext(data))

    def puts(self, data):
        """
        Write data content to the output device with the '\n' (POSIX) or '\r\n' (Windows) at the end.

        :param data: bytes
        :return: None
        """
        self.write(data)
        self.__output.write(os.linesep)


# pylint: disable=C0103, W0201
otty = SystemOutput(sys.stdout)
otty.i18n = SystemOutput(sys.stdout, __)

etty = SystemOutput(sys.stderr)
etty.i18n = SystemOutput(sys.stderr, __)
# pylint: enable=C0103, W0201


class _BaseOutput(object):
    """
    Basic output.
    """

    _ident = " "

    symbols_ascii = {
        "leaf": "\\_",
        "bullet": "*",
        "list": "  -",
        "n/a": " <N/A>",
    }

    symbols_utf = {
        "leaf": "\u2514\u2510",
        "bullet": chr(0x25a0),
        "list": "\u2514\u2500",
        "n/a": "N/A",
    }

    colors_16 = {
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

    colors_256 = {
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
        :return: Colors dictionary for the specific scheme
        """
        return getattr(self, "colors_{}".format(self._colors))

    def _get_symbol_scheme(self):
        """
        Get symbols scheme
        :return: Symbols dictionary for the specific scheme
        """
        return getattr(self, "symbols_{}".format(self._encoding))

    def c_type(self, value):
        """
        Color type.

        :param value: Value of the color
        :return: colored string
        """
        return self._get_color_scheme()["types"].get(type(value).__name__, colored.attr("reset"))

    def c_leaf(self, offset):
        """
        Insert leaf.

        :param offset: leaf offset on the printing output
        :return: colored string
        """
        return "{}{}".format(offset + self._ident, self._get_symbol_scheme()["leaf"])

    def c_na(self, offset):
        """
        Insert value or N/A.

        :param offset: leaf offset on the printing output
        :return: colored string
        """
        return "{}{}{}{}".format(offset + self._ident, self._get_color_scheme()["elements"]["n/a"],
                                 self._get_symbol_scheme()["n/a"], colored.attr("reset"))

    def paint(self, obj, offset=""):
        """
        Paint an object on the screen.

        :param obj: object to process
        :param offset: leaf offset on the printing output
        :raises NotImplementedError: this method must be overridden.
        :return: colored string
        """
        raise NotImplementedError("Not implemented")


class MappingOutput(_BaseOutput):
    """
    Output dictionary.
    """
    def c_key(self):
        """
        Color key.

        :return: colored string
        """
        return self._get_color_scheme()["elements"]["key"]

    def paint(self, obj, offset=""):
        """
        Paint mapping output.

        :param obj: object to output (a map)
        :param offset: leaf offset on the printing output
        :return: colored string
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
                                          encoding=self._encoding).paint(value, offset=offset + self._ident))
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

        :param obj: object to putput (list)
        :param offset: leaf offset on the printing output
        :return: colored string
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
    STYLE_ALRT = "alert"
    STYLE_WARN = "warning"
    STYLE_SCCS = "success"
    STYLE_INFO = "info"

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

        :return: color style
        """
        return self.__class__.__dict__.get("_styles_{}".format(self._colors), self._styles_16)

    def _get_suffix(self):
        """
        Get suffix.

        :return: color suffix
        """
        return self.__class__.__dict__.get("_suffix_{}".format(self._encoding), self._suffix_ascii)

    def add(self, title, style=STYLE_INFO):
        """
        Add title.

        :param title: Text
        :param style: style name
        :return: None
        """
        self._titles[__(title)] = style

    def paint(self, text):
        """
        Paint a title.

        :param text: Text
        :return: colored title
        """
        text = __(text)
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


class Highlighter(object):
    """
    Highlights something on just one line.
    """
    _style_16 = {
        "base": 10,
        "hi": 10,
        "lo": 3,
    }

    _style_256 = {
        "base": 184,
        "hi": 82,
        "lo": 172,
    }

    def __init__(self, colors=16):
        self._colors = colors

    def _get_style(self):
        return getattr(self, "_style_{}".format(self._colors))

    def paint(self, pattern, **highlights):
        """
        Highlight data.
        Example:

           paint("something dimmed {foo} and highlighted {bar}",
                 foo=("here", "lo"), bar=("here", "hi"))

        :param pattern: Pattern to interpolate with
        :param highlights: Highlights that are be emphasised in the pattern
        :return: colored string
        """
        hlts = {}
        for element, attrs in highlights.items():
            text, mode = attrs
            hlts[element] = "{f}{t}{b}".format(f=colored.fg(self._get_style()[mode]), t=text,
                                               b=colored.fg(self._get_style()["base"]))

        return "{b}{c}{r}".format(b=colored.fg(self._get_style()["base"]),
                                  c=pattern.format(**hlts),
                                  r=colored.attr("reset"))


class ConsoleMessages(object):
    """
    Console CLI colored output.
    This provides standard interface to all
    non-logging messages outside.
    """
    _style_16 = {
        "info": 6,
        "warning": 3,
        "error": 1,
        "bold": {
            "info": 14,
            "warning": 11,
            "error": 9,
        }
    }

    _style_256 = {
        "info": 40,
        "warning": 208,
        "error": 160,
        "bold": {
            "info": 82,
            "warning": 214,
            "error": 196,
        }
    }

    def __init__(self, colors=16, encoding="ascii"):
        self._colors = colors
        self._encoding = encoding

    def __style(self):
        return getattr(self, "_style_{}".format(self._colors))

    def _emph(self, text, section):
        """
        Emphasis.

        :param text: text to emphasise
        :param section: section of the emphasis
        :return: Colored string
        """
        out = []
        bold = False
        for char in text:
            if char == "*":
                bold = not bold
                out.append(colored.attr("bold") if bold else colored.attr("res_bold"))
                out.append(colored.fg(self.__style()["bold"][section]) if bold else colored.fg(self.__style()[section]))
            else:
                out.append(char)

        return ''.join(out)

    def _standard(self, message, *args, **kwargs):
        """
        Standard output for info and input.

        :param message: text message
        :param args: values to format the message
        :param kwargs: keyword arguments to format the message
        :return: colored string
        """
        return self._emph("{}{}{}".format(colored.fg(self.__style()["info"]),
                                          __(message).format(*args, **kwargs), colored.attr("reset")), "info")

    def input(self, message, *args, **kwargs):
        """
        Display input (like info, just no new line).

        :param message: text message
        :param args: values to format the message
        :param kwargs: keyword arguments to format the message
        :return: colored string
        """
        otty.write(self._standard(message, *args, **kwargs))

    def info(self, message, *args, **kwargs):
        """
        Display info.

        :param message: text message
        :param args: values to format the message
        :param kwargs: keyword arguments to format the message
        :return: colored string
        """
        otty.puts(self._standard(message, *args, **kwargs))

    def warning(self, message, *args, **kwargs):
        """
        Display warning message.

        :param message: text message
        :param args: values to format the message
        :param kwargs: keyword arguments to format the message
        :return: colored string
        """
        message = __(message)
        otty.puts(self._emph("{}{}{}".format(colored.fg(self.__style()["warning"]),
                                             __(message).format(*args, **kwargs), colored.attr("reset")),
                             "warning"))

    def error(self, message, *args, **kwargs):
        """
        Display error message.

        :param message: text message
        :param args: values to format the message
        :param kwargs: keyword arguments to format the message
        :return: colored string
        """
        otty.puts(self._emph("{}{}{}".format(colored.fg(self.__style()["error"]),
                                             __(message).format(*args, **kwargs), colored.attr("reset")), "error"))
