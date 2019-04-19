# coding: utf-8
"""
State collector is to incrementally collect state source tree.
The state might be one file, or might include resources. This
must be compiled on the client side and make sure that the
conditions are met. For example, conditions might or might not
include more resources, which are still are not on the client.
This approach allows to compile till some degree and request
for further part from the server.

The downside of this approach that the state is compiled multiple
times unless it finally resolves all the pieces. However, client
is transferring only what is needed for the particular task,
instead of copying the entire library of formulas, available on
the server.
"""
import os
import shutil
from sugar.lib.compiler import ObjectResolver


class StateCollector:
    """
    State collector will create a path of /DEFAULT_ROOT/JID for
    each state job and then there will assemble the further
    pieces, concurrently.
    """
    DEFAULT_ROOT = "/var/cache/sugar/client/states"

    def __init__(self, jid, root=None):
        self._base_root = root or self.DEFAULT_ROOT
        self._jid = jid

    def state_root(self) -> str:
        """
        Returns state root of BASE_ROOT/JID.

        :return: path of the state root.
        """
        return os.path.join(self._base_root, self._jid)

    def cleanup(self) -> None:
        """
        Cleanup the data after job is finished.

        :return: None
        """
