# coding: utf-8
"""
Storage of the client arbitrary graph-like data
and UCS algorithm implementation to search over it.
"""
import os
import errno
import pickle
import collections

import sugar.utils.files
from sugar.lib.logger.manager import get_logger

# pylint: disable=C0103,W0622


class CDataContainer:
    """
    Data container structure
    """

    def __init__(self, id: str, host: str):
        """
        :param id: machine ID
        :param host: IP addr or FQDN
        """
        self.id = id
        self.host = host
        self.traits = {}
        self.inherencies = {}


# pylint: enable=C0103,W0622

class CDataStore:
    """
    Data storage/retriever in the directory.
    """
    DEFAULT_CACHE_DIR = "/var/cache"  # TODO: add OSes

    def __init__(self, root_path=None):
        self.log = get_logger(self)
        self.__r_path = os.path.join(root_path or self.DEFAULT_CACHE_DIR, "sugar", "cdata")
        try:
            os.makedirs(self.__r_path, mode=0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                self.log.error("Error creating client storage directory '{}': {}", self.__r_path, exc)

    def _get_node_path(self, container: CDataContainer) -> str:
        """
        Get node path from the container data.

        :param container: container of the data for serialisation
        :return: path for the given node.
        """
        return os.path.join(self.__r_path, "{}.data".format(container.id))

    def add(self, container: CDataContainer) -> None:
        """
        Add a client by machine_id.

        :param container: container of the data for the serialisation
        :return: None
        """
        self.remove(container)
        with sugar.utils.files.fopen(self._get_node_path(container), "wb") as nph:
            pickle.dump(container, nph, pickle.HIGHEST_PROTOCOL)

    def remove(self, container: CDataContainer) -> None:
        """
        Remove a client by machine id.

        :param container: container of the data for the serialisation
        :return: None
        """
        node_path = self._get_node_path(container)
        try:
            os.unlink(node_path)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                self.log.error("Error removing obsolete node data '{}': {}", node_path, exc)

    def clients(self) -> collections.Iterable:
        """
        Return top nodes of the store.

        :return: CDataContainer object
        """
        for mid in os.listdir(self.__r_path):
            with sugar.utils.files.fopen(os.path.join(self.__r_path, mid), "rb") as nph:
                yield pickle.load(nph)
