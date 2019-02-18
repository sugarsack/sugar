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

from sugar.components.server.pdatamatch import UniformMatch
from sugar.components.server.qelement import QueryBlock


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
        :param subset: subeset of hosts meta (a copy in memory)
        :return: list of hosts
        """
        for clause in queries:
            _subset = []
            for host_meta in subset:
                if UniformMatch(host_meta).match(clause):
                    _subset.append(host_meta)
            subset = _subset

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
