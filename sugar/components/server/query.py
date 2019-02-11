# coding: utf-8
"""
Query parser.

Sugar query can include everything in one go
and switch between query type (UNIX matcher
or regular expressions).

Semantics:

    [trait]:[flags]:<target>

Traits:
    Any Sugar known trait.

Flags (all optional):
    r: The target contains or is a regular expression.
       By default they are UNIX matching.

    c: Case sensitive (by default is not)

    x: Exclude (inversion)

    a: All, an alias to escaped '\*' globbing.
       NOTE: this flag invalidates everything,
       turning all query into just "*".

Query may contain multiple blocks as above, separated
by a slash (/). Comma separates lists in values.

Single slash (/) means "substract". Subsequent query will
select from the set of items of previous result.

Double slash (//) means "union".Subsequent query will
select from all items.

Examples:

    os-family:-rc:(Debian|RedHat)/hostname:web[1,3]

    ip-addr:*123/os-family:debian/:-r:web-(dev|uat)

    os-family:-r:(debian|ubuntu)/ip-addr:-x:192*

    hostname:web1,web2,web3//os-family:debian
"""

import re
import time
import fnmatch

import sugar.lib.exceptions


class QueryBlock:
    """
    Query block.
    """
    FLAGS = {
        "r": "Following is a regular expression",
        "c": "Case-sensitive of the following",
        "x": "Inverse of the following",
        "a": "All items",
    }

    def __init__(self, raw: str):
        """
        Parse raw query block.

        :param raw: query block string
        """
        self.flags = ()
        self.trait = None
        self.target = None

        raw = raw.strip() if raw is not None else None
        if raw:
            self.__classify(raw)

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
            self.trait = None
            self.flags = ()
        else:
            assert flags.startswith("-"), "Flags must always start with '-', unless 'a' for 'all'"
            self.flags = set(flags[1:])
            for flag in self.flags:
                assert flag in self.FLAGS, "Unknown flag: '{}'".format(flag)

            if "c" not in self.flags:
                self.target = self.target.lower()
            if "r" not in self.flags and "," in self.target:
                self.target = "({})".format("|".join(self.target.split(",")))
                self.flags.add("r")
            if "r" not in self.flags:
                self.target = fnmatch.translate(self.target)

        if not self.trait:
            self.trait = None
        if not self.target:
            self.target = None
        self.flags = tuple(self.flags)

    def _full(self, raw: str) -> None:
        """
        Parse full query.

        :param raw: query block
        :return: None
        """
        self.trait, flags, self.target = raw.split(":")
        self._get_flags(flags)

    def _partial(self, raw: str) -> None:
        """
        Parse partial query.

        :param raw: query block
        :return: None
        """
        self.trait, self.target = raw.split(":")

        # Handle ':a' and 'a:'
        if self.trait == "a" and not self.target or not self.trait and self.target == "a":
            self.trait = None
            self._get_flags("a")

    def _simple(self, raw: str) -> None:
        """
        Simple query.

        :param raw: query block
        :return: None
        """
        if "," in raw and "[" not in raw and "]" not in raw:
            self.target = "({})".format("|".join(raw.split(",")))
            self.flags = ("r",)
        else:
            self.target = fnmatch.translate(raw)


class Query:
    """
    Query parser class.
    """

    def __init__(self, raw):
        """
        Parse raw query.

        :param raw: query string.
        """
        self.__blocks = []
        self._set_blocks(raw)

    def _set_blocks(self, raw: str) -> None:
        """
        Set query blocks.

        :param raw: query string with possibly multuple blocks, delimited by "/" (slash).
        :return: None
        """
        temp_delim = "--{}=D={}".format(*str(time.time()).split("."))
        for qstr in [q_block.replace(temp_delim, "/") for q_block in raw.replace("\\/", temp_delim).split("/")]:
            qstr = qstr.strip()
            self.__blocks.append(QueryBlock(qstr))

    def filter(self, *hosts):
        """
        Filter hosts.

        :param hosts: original hosts.
        :return: filtered hosts
        """
        # TODO: Here also filter traits
        pass

        # Filter hostnames
        for clause in self.__blocks:
            regex = re.compile(clause.target)
            if "x" not in clause.flags:
                hosts = list(filter(regex.search, hosts))
            else:
                _hosts = []
                for host in hosts:
                    if not regex.search(host):
                        _hosts.append(host)
                hosts = _hosts
                del _hosts

        return hosts
