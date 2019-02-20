# coding: utf-8
"""
Storage of the client arbitrary graph-like data
and UCS algorithm implementation to search over it.
"""
import os
import errno
import pickle
import pathlib
import shutil
import collections

import sugar.utils.files
from sugar.lib.logger.manager import get_logger

# pylint: disable=C0103,W0622


class PDataContainer:
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
        self.pdata = {}


# pylint: enable=C0103,W0622

class PDataStore:
    """
    Data storage/retriever in the directory.
    """
    DEFAULT_CACHE_DIR = "/var/cache"  # TODO: add OSes

    def __init__(self, root_path=None):
        self.log = get_logger(self)
        self.log.debug("Initialising P-Data store")
        self.__r_path = os.path.join(root_path or self.DEFAULT_CACHE_DIR, "sugar", "cdata")
        self._create_r_path()

    def _create_r_path(self) -> None:
        """
        Create root path.

        :return: None
        """
        assert len(pathlib.Path(self.__r_path).parents) > 1, "Path '{}' seems too short".format(self.__r_path)
        try:
            os.makedirs(self.__r_path, mode=0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                self.log.error("Error creating client storage directory '{}': {}", self.__r_path, exc)

    def _get_node_path(self, container: PDataContainer) -> str:
        """
        Get node path from the container data.

        :param container: container of the data for serialisation
        :return: path for the given node.
        """
        return os.path.join(self.__r_path, "{}.data".format(container.id))

    def add(self, container: PDataContainer) -> None:
        """
        Add a client by machine_id.

        :param container: container of the data for the serialisation
        :return: None
        """
        self.remove(container)
        node_path = self._get_node_path(container)
        with sugar.utils.files.fopen(node_path, "wb") as nph:
            self.log.debug("Adding node at '{}'", node_path)
            pickle.dump(container, nph, pickle.HIGHEST_PROTOCOL)

    def remove(self, container: PDataContainer) -> None:
        """
        Remove a client by machine id.

        :param container: container of the data for the serialisation
        :return: None
        """
        node_path = self._get_node_path(container)
        try:
            self.log.debug("Removing node at '{}'", node_path)
            os.unlink(node_path)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                self.log.error("Error removing obsolete node data '{}': {}", node_path, exc)

    def flush(self) -> None:
        """
        Flushes the entire store.

        :return: None
        """
        path = pathlib.Path(self.__r_path)
        if path.exists():
            self.log.debug("Removing the entire store data at '{}'", path.parents[0])
            shutil.rmtree(str(path.parents[0]))
            self.log.debug("Creating data store space at '{}'", self.__r_path)
            self._create_r_path()

    def clients(self, active=None) -> collections.Iterable:
        """
        Return top nodes of the store.

        :return: PDataContainer object
        """
        for mid_file in os.listdir(self.__r_path):
            mid = mid_file.split(".")[0]
            if active is None or mid in active:
                with sugar.utils.files.fopen(os.path.join(self.__r_path, mid_file), "rb") as nph:
                    yield pickle.load(nph)
