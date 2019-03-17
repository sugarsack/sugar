# coding: utf-8
"""
Client registry and matcher.

- Match clients by the query (query parser, basically)
- General glob by name
- Traits glob by attributes and values
- Deferred command state (happens when command has been issued by client was down).
  This allows us to send a commands to the clients, once they are up.
"""
from sugar.utils.objects import Singleton
from sugar.utils.structs import ImmutableDict
from sugar.lib.logger.manager import get_logger
from sugar.config import get_config
from sugar.components.server.pdatastore import PDataStore
from sugar.components.server.query import Query


@Singleton
class RuntimeRegistry:
    """
    Registry of current online clients.
    """
    def __init__(self):
        self.__peers = {}
        self.pdata_store = PDataStore(get_config().cache.path)
        self.log = get_logger(self)
        self.__keystore = None

    @property
    def keystore(self):
        """
        Get keystore.

        :return: keystore
        """
        return self.__keystore

    @keystore.setter
    def keystore(self, keystore):
        """
        Set keystore.

        :param keystore: the keystore instance
        :return: None
        """
        if self.keystore is None:
            self.__keystore = keystore

    @property
    def peers(self) -> ImmutableDict:
        """
        Return read-only peers.

        :return: dictionary of peers (read-only)
        """
        return ImmutableDict(self.__peers)

    def register(self, machine_id, peer) -> None:
        """
        Register peer.

        :param machine_id: a machine ID string
        :param peer: a peer protocol
        :return: None
        """
        if machine_id:
            self.__peers.setdefault(machine_id, peer)
            self.log.debug("Registered peer with the ID: {}", machine_id)
        else:
            self.log.error("Machine ID should be specified, '{}' is passed instead", repr(machine_id))

    def unregister(self, machine_id: str) -> None:
        """
        Unregister peer.

        :param machine_id: Machine ID string
        :return: None
        """
        try:
            del self.__peers[machine_id]
            self.log.debug("Unregistered peer with the ID: {}", machine_id)
        except KeyError:
            self.log.error("Peer ID {} was not found to be unregistered.", repr(machine_id))

    def get_hostname(self, machine_id: str) -> str:
        """
        Get hostname by the machine ID.

        :param machine_id: Machine ID string
        :return: hostname
        """
        keyobj = self.keystore.get_key_by_machine_id(machine_id)
        return next(iter(keyobj)).hostname if keyobj is not None and keyobj else None

    def get_targets(self, query: str) -> list:
        """
        Return target clients for the given query.

        :param query: query string from the caller
        :return: list of machine-id to which target the messages by the query
        """
        return Query(query).filter(list(self.pdata_store.clients(active=self.__peers.keys())))

    def get_status(self):
        """
        Return clients minimal data (no p-data) and their status (offline/online).
        :return: list of machines with their statuses.
        """
        systems = {}
        for pd_container in self.pdata_store.clients():
            del pd_container.pdata
            del pd_container.traits
            pd_container.online = pd_container.id in self.__peers.keys()
            systems[pd_container.id] = pd_container

        return systems
