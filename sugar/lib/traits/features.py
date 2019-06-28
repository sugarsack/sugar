"""
Sugar traits core.
"""

from __future__ import absolute_import, unicode_literals

from sugar.lib.traits.decorators import trait
import sugar.lib.traits.utils
import sugar.utils.network


@trait("machine-id")
def machine_id():
    """
    Provide the machine-id for
    machine/virtualization combination

    :return: Machine ID string
    """
    return sugar.lib.traits.utils.get_trait_func("get_machine_id")()


@trait("host")
def host_name():
    """
    Provide hostname.

    :return: hostname string
    """
    return sugar.utils.network.get_fqhostname().partition(".")[0]


@trait("domain")
def domain_name():
    """
    Provide domain name

    :return: domain name string
    """
    return sugar.utils.network.get_fqhostname().partition(".")[-1]


@trait("host-fqdn")
def host_name_fqdn():
    """
    Provide hostname FQDN

    :return: hostname FQDN string
    """
    return sugar.utils.network.get_fqhostname()


@trait("pkg-manager")
def package_manager():
    """
    Provide the name of the package manager.

    :return:
    """
    return sugar.lib.traits.utils.get_trait_func("get_package_manager")()


@trait("os-family")
def os_family():
    """
    Provide OS family.

    :return:
    """
    return sugar.lib.traits.utils.get_trait_func("get_os_family")()


@trait("os-arch")
def os_arch():
    """

    :return:
    """
    return sugar.lib.traits.utils.get_trait_func("get_os_architecture")()
