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

Query may contain multiple blocks as above, separated
by a comma.

Examples:

    os-family:rc:(Debian|RedHat),hostname:web[1,3]
    ipv4:*123,os-family:debian,:r:web-(dev|uat)
"""

import re
import fnmatch


class QueryBlock:
    """
    Query block.
    """
    def __init__(self, raw):
        """
        Parse raw query block.

        :param raw: query block string
        """
        self.flags = []
        self.trait = None
        self.target = None


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

        :param raw: query string with possibly multuple blocks.
        :return: None
        """
        for qstr in raw.split(","):
            qstr = qstr.strip()
            self.__blocks.append(QueryBlock(qstr))

    def __iter__(self):
        for query_block in self.__blocks:
            yield query_block
