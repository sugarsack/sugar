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
