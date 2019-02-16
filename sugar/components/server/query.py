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

    a: All, an alias to escaped '*' globbing.
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
from sugar.components.server.cdatastore import CDataContainer


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


class Query:
    """
    Query parser class.
    """

    def __init__(self, raw):
        """
        Parse raw query.

        :param raw: query string.
        """
        self.__uniform = False
        self.__blocks = []
        self.__p_blocks = []
        self._set_blocks(raw)

    @property
    def is_uniform(self) -> bool:
        """
        Return True if query is expecting data
        structure for the uniform search.

        :return: True if uniform
        """
        return bool(self.__uniform)

    @staticmethod
    def _or(raw: str, temp_delimeter: str) -> list:
        """
        Get parallel blocks by OR operator.
        Supported syntax: //, ||, " or ".

        :param raw: query parallel block
        :param temp_delimeter: temporary delimeter to stash escaped slashes in case "//" is used.
        :return: parallel blocks
        """
        raw = raw.replace("\\/", temp_delimeter)
        if " or " in raw:
            p_blocks = re.sub(r"\s+", " ", raw).split(" or ")
        elif "||" in raw:
            p_blocks = re.split(r"\s+\|\|\s+|\s+\|\||\|\|\s+|\|\|", raw)
        else:
            p_blocks = re.split(r"\s+//\s+|\s+//|//\s+|//", raw)

        return p_blocks

    @staticmethod
    def _and(raw: str, temp_delimeter: str) -> list:
        """
        Get serial blocks by AND operator.
        Supported syntax: /, &&, " and ".

        :param raw: query serial block
        :return: serial blocks
        """
        if " and " in raw:
            s_blocks = re.sub(r"\s+", " ", raw).split(" and ")
        elif "&&" in raw:
            s_blocks = re.split(r"\s+&&\s+|\s+&&|&&\s+|&&", raw)
        else:
            s_blocks = re.split(r"\s+/\s+|\s+/|/\s+|/", raw)

        return [qstr.replace(temp_delimeter, "/") for qstr in s_blocks]

    def _set_blocks(self, raw: str) -> None:
        """
        Set query blocks.

        :param raw: query string with possibly multuple blocks, delimited by "/" (slash).
        :return: None
        """
        temp_delim = "--{}=D={}".format(*str(time.time()).split("."))
        for p_block in self._or(raw, temp_delimeter=temp_delim):
            op = QueryBlock.OPERANDS["//"]     # pylint: disable=C0103
            q_block = []
            for q_str in self._and(p_block, temp_delimeter=temp_delim):
                query = QueryBlock(q_str, operand=op)
                if not self.is_uniform:
                    self.__uniform = bool(query.trait)
                self.__blocks.append(query)
                q_block.append(query)
                op = QueryBlock.OPERANDS["/"]  # pylint: disable=C0103
            if q_block:
                self.__p_blocks.append(q_block)

    def explain(self):
        """
        Explain query.

        :return: explanation str
        """
        out = ["Match clients"]
        first = True
        for block in self.__blocks:
            if not first:
                out.append(block.op)
            out.append("where")
            if block.trait:
                out.append("trait '{}'".format(block.trait))
            if block.target:
                out.append("target is")
                if not block.flags:
                    out.append("globbing of")
                else:
                    for flag in block.flags:
                        out.append(QueryBlock.FLAGS[flag])
                out.append("'{}'".format(block._orig_target if "r" not in block.flags  # pylint: disable=W0212
                                         else block.target))
            first = False

        return " ".join(out)

    @staticmethod
    def __filter_within(queries, subset):
        """
        Filter within the subset.

        :param blocks: queries
        :param hosts: subset of hosts
        :return: list of hosts
        """
        for clause in queries:
            regex = re.compile(clause.target)
            if "x" not in clause.flags:
                subset = list(filter(regex.search, subset))
            else:
                _hosts = []
                for host in subset:
                    if not regex.search(host):
                        _hosts.append(host)
                subset = _hosts
                del _hosts

        return subset

    @staticmethod
    def __filter_uniform_within(queries: list, subset: list) -> list:
        """
        Filter uniform data within the subset.

        :param queries: queries
        :param subset: subeset of hosts meta
        :return: list of hosts
        """

        return subset

    def filter(self, hosts: list) -> list:
        """
        Filter hosts.

        :param hosts: lists of hosts
        :return: filtered out list of hosts
        """
        result = []
        data_filter = self.__filter_uniform_within if self.is_uniform else self.__filter_within
        for seq_queries in self.__p_blocks:
            result += data_filter(seq_queries, hosts[::])

        return list(set(result))
