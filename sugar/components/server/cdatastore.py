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


class CDataContainer:
    """
    Data container structure
    """

    def __init__(self, id: str):
        """
        :param id: machine ID
        """
        self.id = id
        self.traits = {}
        self.inherencies = {}


class CDataStore:
    """
    Data storage/retriever in the directory.
    """
    DEFAULT_CACHE_DIR = "/var/cache"  # TODO: add OSes

    def __init__(self, root_path=None):
        self.log = get_logger(self)
        if root_path is None:
            root_path = os.path.join(self.DEFAULT_CACHE_DIR, "sugar", "cdata")
        self.__r_path = root_path
        try:
            os.makedirs(self.__r_path, mode=0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                self.log.error("Error creating client storage directory '{}': {}", self.__r_path, exc)

    def add(self, container: CDataContainer) -> None:
        """
        Add a client by machine_id.

        :param container: container of the data for the serialisation
        :return: None
        """
        node_path = os.path.join(self.__r_path, "{}.data".format(container.id))
        try:
            os.unlink(node_path)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                self.log.error("Error removing obsolete node data '{}': {}", node_path, exc)

        with sugar.utils.files.fopen(node_path, "wb") as nph:
            pickle.dump(container, nph, pickle.HIGHEST_PROTOCOL)

    def clients(self) -> collections.Iterable:
        """
        Return top nodes of the store.

        :return: CDataContainer object
        """
        for mid in os.listdir(self.__r_path):
            with sugar.utils.files.fopen(os.path.join(self.__r_path, mid), "rb") as nph:
                yield pickle.load(nph)
