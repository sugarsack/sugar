# coding: utf-8
"""
Query block element, a part of the query compound.
"""

import fnmatch
import sugar.lib.exceptions


class QueryBlock:
    """
    Query block.
    """
    FLAGS = {
        "r": "a reg-exp",
        "c": "is case-sensitive",
        "x": "an inversion of",
        "a": "matches everything",
        "d": "client data",
    }

    OPERANDS = {
        "/": "and",
        "//": "or",
    }

    def __init__(self, raw: str, operand=None):
        """
        Parse raw query block.

        :param raw: query block string
        """
        self.flags = ()
        self.trait = None
        self.path = []  # Slicer path (see "sugar.utils.structs.path_slice")
        self.target = None
        self._orig_target = None
        self.op = operand or self.OPERANDS["/"]  # pylint: disable=C0103

        raw = raw.strip() if raw is not None else None
        if raw:
            self.__classify(raw)
        if self.trait:
            self.path = self.trait.split(".")

    @property
    def by_trait(self) -> bool:
        """
        This query targeting a trait.

        :return: boolean
        """
        return bool(self.trait)

    def __classify(self, raw: str) -> None:
        """
        Parse any kind of query.

        :param raw: query string
        :return: None
        """
        if raw.count(":") == 2:
            self._full(raw)
        elif raw.count(":") == 1:
            self._partial(raw)
        elif raw.count(":") > 2:
            raise sugar.lib.exceptions.SugarException("Query is not understood: '{}'".format(raw))
        else:
            self._simple(raw)

    def _get_flags(self, flags: str) -> None:
        """
        Validate flags.

        :param flags: flags
        :return: None
        """
        if "a" in flags:
            self.target = fnmatch.translate("*")
            self._orig_target = "*"
            self.trait = None
            self.flags = ()
        else:
            self.flags = set(flags)
            for flag in self.flags:
                assert flag in self.FLAGS, "Unknown flag: '{}'".format(flag)

            if "c" not in self.flags:
                self.target = self.target.lower()
            if "r" not in self.flags:
                target = self._list_to_regex(self.target)
                if target != self.target:
                    self.target = target
                    self.flags.add("r")
            if "r" not in self.flags:
                self.target = fnmatch.translate(self.target)

        if not self.trait:
            self.trait = None
        if not self.target:
            self.target = None
        self.flags = tuple(self.flags)

    @staticmethod
    def _list_to_regex(raw: str) -> str:
        """
        Convert list of items to a regex.

        :param raw: query data
        :return: regex
        """
        if "," in raw and "[" not in raw and "]" not in raw:
            raw = "({})".format("|".join([fnmatch.translate(item) for item in raw.split(",")]))

        return raw

    def _full(self, raw: str) -> None:
        """
        Parse full query.

        :param raw: query block
        :return: None
        """
        self.trait, flags, self.target = raw.split(":")
        self._orig_target = self.target
        self._get_flags(flags)

    def _partial(self, raw: str) -> None:
        """
        Parse partial query.

        :param raw: query block
        :return: None
        """
        self.trait, self.target = raw.split(":")
        self.flags = ""
        self._orig_target = self.target

        # Handle ':a' and 'a:'
        if self.trait == "a" and not self.target or not self.trait and self.target == "a":
            self.trait = None
            self._get_flags("a")
        else:
            self._get_flags(self.flags)

    def _simple(self, raw: str) -> None:
        """
        Simple query.

        :param raw: query block
        :return: None
        """
        self._orig_target = raw
        self.target = self._list_to_regex(raw)
        if self.target != raw:
            self.flags = ("r",)
        else:
            self.target = fnmatch.translate(raw)
