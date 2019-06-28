"""
Linux traits implementations
"""
import os
import shutil
import typing
import sugar.utils.files


def get_machine_id() -> typing.Optional[typing.AnyStr]:
    """
    Get machine ID

    :return: string of the machine ID
    """
    ret = None
    for loc in [loc for loc in ['/etc/machine-id', '/var/lib/dbus/machine-id'] if os.path.exists(loc)]:
        with sugar.utils.files.fopen(loc) as mfh:
            ret = mfh.read().strip() or None
            if ret:
                break

    return ret


def get_package_manager() -> typing.Optional[typing.AnyStr]:
    """
    Get package manager of the current Linux distro.
    If package manager cannot be found, this function will return just None.

    NOTE: The names are conventional, e.g. on Debian with dpkg, apt-get,
          apt-cache etc it will return just "apt".

    :return: string of the package manager name.
    """
    packmans = {"zypper": None, "apt": None, "apt-get": "apt", "yum": None, "dnf": None}
    package_manager = None
    for pm_name, pm_alias in packmans.items():
        if shutil.which(pm_name):
            package_manager = pm_alias or pm_name
            break

    return package_manager


def get_os_family() -> typing.Optional[typing.AnyStr]:
    """
    Get OS family.

    :return:
    """
    return "debian"


def get_os_architecture() -> typing.AnyStr:
    """
    Get OS architecture on all known distributions of Linux.

    :return: string architecture as related to the packaging manager, e.g. "amd64" on Debian and "x86_64" on RH/CentOS
    """
    os_family = get_os_family()
    os_arch = ""

    if os_family == "debian":
        stdout, _ = sugar.utils.process.run_outerr("dpkg", args=["--print-architecture"])
        os_arch = stdout.strip()
    elif os_family in ["redhat", "suse"]:
        os_arch = ''.join([x for x in platform.uname()[-2:] if x][-1:])

    return os_arch
