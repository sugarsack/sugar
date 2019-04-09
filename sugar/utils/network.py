"""
Network utilities.
"""
from __future__ import absolute_import, unicode_literals

import socket

from sugar.lib.logger.manager import get_logger

log = get_logger(__name__)  # pylint: disable=C0103


def get_fqhostname():
    """
    Returns the fully qualified hostname

    :return: FQDN string or None
    """
    # try getaddrinfo()
    fqdn = None
    try:
        addrinfo = socket.getaddrinfo(
            socket.gethostname(), 0, socket.AF_UNSPEC, socket.SOCK_STREAM,
            socket.SOL_TCP, socket.AI_CANONNAME
        )
        for info in addrinfo:
            # info struct [family, socktype, proto, canonname, sockaddr]
            # On Windows `canonname` can be an empty string
            # This can cause the function to return `None`
            if len(info) > 3 and info[3]:
                fqdn = info[3]
                break
    except socket.gaierror:
        pass  # NOTE: this used to log.error() but it was later disabled
    except socket.error as err:
        log.debug('socket.getaddrinfo() failure while finding fqdn: %s', err)
    if fqdn is None:
        fqdn = socket.getfqdn()

    return fqdn


class _IPvX:
    def __init__(self, fqdn):
        self._fqdn = fqdn

    @staticmethod
    def __get_ip(fqdn, family):
        """
        Get IP address by FQDN.

        :param fqdn:
        :return:
        """
        addr = None
        for struct in socket.getaddrinfo(fqdn, None):
            _family, _type, _proto, _canonname, _sockaddr = struct
            if family == _family:
                addr = _sockaddr[0]
                break
        return addr

    def get_ipv4(self):
        """
        Get IPv4 primary address.

        :return:
        """
        return self.__get_ip(self._fqdn, socket.AF_INET)

    def get_ipv6(self):
        """
        Get IPv6 primary address.

        :return:
        """
        return self.__get_ip(self._fqdn, socket.AF_INET6)


def get_ipv4(fqdn) -> str:
    """
    Get IPv4 address from the fqdn.
    :param fqdn:
    :return:
    """
    return _IPvX(fqdn).get_ipv4()


def get_ipv6(fqdn) -> str:
    """
    Get IPv6 address from the fqdn.

    :param fqdn: FQDN
    :return:
    """
    return _IPvX(fqdn).get_ipv6()


def get_hostname(ipv):
    """
    Get hostname from IPv4 and IPv6.

    :param ipv4:
    :return:
    """
    return socket.gethostbyaddr(ipv)[0]
