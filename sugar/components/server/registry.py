# coding: utf-8
"""
Client registry and matcher.

- Match clients by the query (query parser, basically)
- General glob by name
- Traits glob by attributes and values
- Deferred command state (happens when command has been issued by client was down).
  This allows us to send a commands to the clients, once they are up.
"""
import re
import fnmatch

from sugar.utils.objects import Singleton
from sugar.utils.structs import ImmutableDict
from sugar.lib.logger.manager import get_logger


class PeerMatcher:
    """
    Peer matcher class.
    This works only by a hostname for now.
    """
    def __init__(self):
        self.__host_to_mid = {}
        self.log = get_logger(self)

    def add(self, host: str, machine_id: str) -> None:
        """
        Add host to the map.

        :param host: hostname string
        :param machine_id: machine ID string
        :return: None
        """
        self.__host_to_mid.setdefault(host, machine_id)

    def remove(self, host: str) -> None:
        """
        Remove host from the map.

        :param host: hostname string
        :return: None
        """
        try:
            del self.__host_to_mid[host]
        except KeyError:
            self.log.error("Error removing hostname '{}': not in the map", host)

    def match(self, query, regex=False):
        """
        Match hostname by Sugar query.
        This does not include traits.

        :param query: query pattern
        :param regex: flag if query is a regular expression, otherwise UNIX pattern match
        :return: matched hostnames
        """
        if not regex:
            query = fnmatch.translate(query)

        return filter(re.compile(query).search, self.__host_to_mid.keys())


@Singleton
class RuntimeRegistry:
    """
    Registry of current online clients.
    """
    def __init__(self):
        self.__peers = {}
        self.matcher = PeerMatcher()
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
            self.matcher.add(self.get_hostname(machine_id), machine_id)
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
        self.matcher.remove(self.get_hostname(machine_id))

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
