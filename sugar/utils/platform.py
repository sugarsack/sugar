# -*- coding: utf-8 -*-
"""
Functions for identifying which platform a machine is
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import sys


def is_windows():
    """
    Simple function to return if a host is Windows or not
    """
    return sys.platform.startswith('win')


def is_linux():
    """
    Simple function to return if a host is Linux or not.
    Note for a proxy minion, we need to return something else
    """
    return sys.platform.startswith('linux')


def is_darwin():
    """
    Simple function to return if a host is Darwin (macOS) or not
    """
    return sys.platform.startswith('darwin')


def is_sunos():
    """
    Simple function to return if host is SunOS or not
    """
    return sys.platform.startswith('sunos')


def is_smartos():
    """
    Simple function to return if host is SmartOS (Illumos) or not
    """
    return os.uname()[3].startswith('joyent_') if is_smartos() else False


def is_smartos_globalzone():
    """
    Function to return if host is SmartOS (Illumos) global zone or not
    """
    glo_zone = False
    if is_smartos():
        try:
            zonename = subprocess.Popen(['zonename'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            glo_zone = not zonename.returncode and zonename.stdout.read().strip() == 'global'
        except OSError:
            pass

    return glo_zone


def is_smartos_zone():
    """
    Function to return if host is SmartOS (Illumos) and not the gz
    """
    zone = False
    if is_smartos():
        try:
            zonename = subprocess.Popen(['zonename'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            zone = not zonename.returncode and zonename.stdout.read().strip() != 'global'
        except OSError:
            pass

    return zone


def is_freebsd():
    """
    Simple function to return if host is FreeBSD or not
    """
    return sys.platform.startswith('freebsd')


def is_netbsd():
    """
    Simple function to return if host is NetBSD or not
    """
    return sys.platform.startswith('netbsd')


def is_openbsd():
    """
    Simple function to return if host is OpenBSD or not
    """
    return sys.platform.startswith('openbsd')


def is_aix():
    """
    Simple function to return if host is AIX or not
    """
    return sys.platform.startswith('aix')
