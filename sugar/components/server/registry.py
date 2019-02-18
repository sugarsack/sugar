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
        if keyobj is not None and keyobj:
            hostname = next(iter(keyobj)).hostname
        else:
            hostname = None

        return hostname

    def get_targets(self, query: str) -> list:
        """
        This returns target clients for the given query.

        :param query: query string from the caller
        :return: list of machine-id to which target the messages by the query
        """
        # This works the following way:
        # 1. Every time something comes or goes away, existing peers
        #    are limiting store result, so the store wont iterate over everything.
        # 2. Store is generating *possible* targets with all the metadata (traits/pdata).
        # 3. Query matcher filtering out what is not needed
        # 4. The result is returned and it already contains traits, pdata and a current hostname

        targets = []
        return targets
