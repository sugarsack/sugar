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


class QueryBlock:
    """
    Query block.
    """
    FLAGS = {
        "r": "a reg-exp",
        "c": "is case-sensitive",
        "x": "an inversion of",
        "a": "matches everything",
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
        self.target = None
        self._orig_target = None
        self.op = operand or self.OPERANDS["/"]  # pylint: disable=C0103

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
            self._orig_target = "*"
            self.trait = None
            self.flags = ()
        else:
            self.flags = set(flags)
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
        self._orig_target = self.target
        self._get_flags(flags)

    def _partial(self, raw: str) -> None:
        """
        Parse partial query.

        :param raw: query block
        :return: None
        """
        self.trait, self.target = raw.split(":")
        self._orig_target = self.target

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
        self._orig_target = raw
        if "," in raw and "[" not in raw and "]" not in raw:
            self.target = "({})".format("|".join([fnmatch.translate(item) for item in raw.split(",")]))
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
        self.__p_blocks = []
        self._set_blocks(raw)

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
        # Filter hostnames
        for clause in queries:
            if clause.trait:  # skip traits selector for now
                continue
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

    def filter(self, hosts: list) -> list:
        """
        Filter hosts.

        :param hosts: lists of hosts
        :return: filtered out list of hosts
        """
        result = []
        for seq_queries in self.__p_blocks:
            result += self.__filter_within(seq_queries, hosts[::])

        return list(set(result))
