# coding: utf-8
"""
Jinja filters for various renderers.
"""
import colored


class JinjaCLIFilters:
    """
    CLI colorisers.
    """

    @staticmethod
    def state(data: str) -> str:
        """
        State code example.

        :param data: string to be colorised
        :return: colorised string
        """
        return "{f}{d}{r}".format(f=colored.fg(3), d=data, r=colored.attr("reset"))

    @staticmethod
    def cli(data: str) -> str:
        """
        Command line code example.

        :param data: string to be colorised
        :return: colorised string
        """
        return "{f}{d}{r}".format(f=colored.fg(10), d=data, r=colored.attr("reset"))

    @staticmethod
    def req(data: str) -> str:
        """
        Required.

        :param data: string to be colorised
        :return: colorised string
        """
        return "{f}{d}{r}".format(f=colored.fg(9), d=data, r=colored.attr("reset"))

    @staticmethod
    def opt(data: str) -> str:
        """
        Optional.

        :param data: string to be colorised
        :return: colorised string
        """
        return "{f}{d}{r}".format(f=colored.fg(12), d=data, r=colored.attr("reset"))

    @staticmethod
    def bold(data: str) -> str:
        """
        CLI bold (highlight text)

        :param data: string to be colorised
        :return: colorised string
        """
        return "{b}{d}{r}".format(b=colored.attr("bold"), d=data, r=colored.attr("reset"))

    @staticmethod
    def marked(data: str) -> str:
        """
        CLI make marked test.

        :param data: string to be colorised
        :return: colorised string
        """
        return "{bg} {b}{fg}{d} {r}".format(bg=colored.bg(8), fg=colored.fg(15), b=colored.attr("bold"),
                                            d=data, r=colored.attr("reset"))
