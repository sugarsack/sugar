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

import sugar.utils.objects
import sugar.utils.structs
from sugar.components.server.pdatastore import CDataContainer
from sugar.components.server.qelement import QueryBlock


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
        sections = []
        if qblock.trait:
            sections.append(sugar.utils.structs.path_slice(self.cdata.pdata, *qblock.path) or {})
        else:
            sections.append(self.cdata.pdata)

        if qblock.trait:
            sections.append(sugar.utils.structs.path_slice(self.cdata.traits, *qblock.path) or {})

        for data in sections:
            ret = self._match(data=data, qblock=qblock)
            if ret:
                break

        return ret

    def _match(self, data, qblock):
        """
        Traverse data by keys.
        Types are supported.

        :return:
        """
        ret = False
        if isinstance(data, dict):
            for d_key in data:
                d_key_alias = d_key.replace(".", "-")  # Alias dots away
                if qblock.trait == d_key_alias:
                    _data = data[d_key]
                    if isinstance(_data, str):
                        _data = sugar.utils.objects.str_to_type(_data)
                    if "c" not in qblock.flags and isinstance(_data, str):
                        _data = _data.lower()
                    if not isinstance(_data, (list, tuple, dict)):
                        _data = [_data]
                    for tgt in _data:
                        if isinstance(tgt, str):
                            ret = bool(re.search(qblock.target, tgt))
                        else:
                            ret = tgt == sugar.utils.objects.str_to_type(qblock._orig_target)  # pylint: disable=W0212
                        if ret:
                            break
                else:
                    if d_key_alias in qblock.path:
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
