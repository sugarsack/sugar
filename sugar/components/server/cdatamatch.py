# coding: utf-8
"""
Client data matcher.

Generally, client data can be arbitrary structure form.
It may contain single elements, sets, maps etc. Example:

- one
- two
- key:
    - value
    - othervalue
    - innerkey:
        - innervalue
        - otherinnerkey: somevalue

Queries:

:d:one
:d:two
key:d:value
key:d:othervalue
key:d:other*
key.innerkey:d:innervalue
key:innerkey.otherinnerkey:d:somevalue

"""
import re

from sugar.components.server.cdatastore import CDataContainer
from sugar.components.server.query import QueryBlock


class UniformMatch:
    """
    Graph data elements search.
    """
    def __init__(self, cdata: CDataContainer):
        self.cdata = cdata

    def match(self, qblock: QueryBlock) -> bool:
        """
        Match structure for the query property.

        :param qblock: Query object.
        :return: boolean
        """
        ret = False
        sections = [self.cdata.inherencies]
        if qblock.trait:
            sections.append(self.cdata.traits)

        for data in sections:
            ret = self._match(data=data, qblock=qblock)
            if ret:
                break

        return ret

    def _match(self, data, qblock):
        """
        Traverse data by keys.

        :return:
        """
        ret = False
        if isinstance(data, dict):
            for d_key in data:
                ret = self._match(data=data[d_key], qblock=qblock)
                if ret:
                    break
        elif isinstance(data, (list, tuple)):
            for elm in data:
                ret = self._match(data=elm, qblock=qblock)
                if ret:
                    break
        else:  # int, bool, str etc
            ret = bool(re.search(qblock.target, data))

        return ret
