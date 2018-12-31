"""
Path utils
"""
from __future__ import absolute_import, print_function, unicode_literals
import collections
import os
import re

import sugar.utils.stringutils
import sugar.utils.platform
from sugar.lib.logger.manager import get_logger

log = get_logger(__name__)  # pylint: disable=C0103


def is_file_or_link(exe):
    """
    Check for os.X_OK doesn't suffice because directory may executable

    :param exe:
    :return:
    """
    return os.access(exe, os.X_OK) and (os.path.isfile(exe) or os.path.islink(exe))


def which(exe=None):
    """
    Python clone of /usr/bin/which
    """
    _path = None
    if not exe:
        log.error("No executable was passed to be searched by sugar.utils.path.which()")
    elif is_file_or_link(exe):
        _path = exe
    else:
        ext_list = sugar.utils.stringutils.to_str(os.environ.get('PATHEXT', str('.EXE'))).split(str(';'))

        def _exe_has_ext():
            """
            Do a case insensitive test if exe has a file extension match in PATHEXT
            """
            ret = False
            for ext in ext_list:
                try:
                    pattern = r'.*\.{0}$'.format(sugar.utils.stringutils.to_unicode(ext).lstrip('.'))
                    re.match(pattern, sugar.utils.stringutils.to_unicode(exe), re.I).groups()
                    ret = True
                    break
                except AttributeError:
                    continue

            return ret

        # Enhance POSIX path for the reliability at some environments, when $PATH is changing
        # This also keeps order, where 'first came, first win' for cases to find optional alternatives
        system_path = sugar.utils.stringutils.to_unicode(os.environ.get('PATH', ''))
        search_path = system_path.split(os.pathsep)
        if not sugar.utils.platform.is_windows():
            search_path.extend([elm for elm in ('/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin')
                                if elm not in search_path])

        for path in search_path:
            full_path = os.path.join(path, exe)
            if is_file_or_link(full_path):
                _path = full_path
                break
            elif sugar.utils.platform.is_windows() and not _exe_has_ext():
                # On Windows, check for any extensions in PATHEXT.
                # Allows both 'cmd' and 'cmd.exe' to be matched.
                for ext in ext_list:
                    # Windows filesystem is case insensitive so we
                    # safely rely on that behavior
                    if is_file_or_link(full_path + ext):
                        _path = full_path + ext
                        break
            if _path is not None:
                break

        log.debug("'%s' could not be found in the following search path: '%s'" % (exe, search_path))

    return _path


def which_bin(exes):
    """
    Scan over some possible executables and return the first one that is found
    """
    bin_path = None
    if isinstance(exes, collections.Iterable):
        for exe in exes:
            path = which(exe)
            if path:
                bin_path = path
                break

    return bin_path
