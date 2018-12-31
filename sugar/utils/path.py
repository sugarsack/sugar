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

log = get_logger(__name__)


def which(exe=None):
    """
    Python clone of /usr/bin/which
    """
    def _is_executable_file_or_link(exe):
        # check for os.X_OK doesn't suffice because directory may executable
        return (os.access(exe, os.X_OK) and
                (os.path.isfile(exe) or os.path.islink(exe)))

    if exe:
        if _is_executable_file_or_link(exe):
            # executable in cwd or fullpath
            return exe

        ext_list = sugar.utils.stringutils.to_str(
            os.environ.get('PATHEXT', str('.EXE'))
        ).split(str(';'))

        def _exe_has_ext():
            """
            Do a case insensitive test if exe has a file extension match in
            PATHEXT
            """
            for ext in ext_list:
                try:
                    pattern = r'.*\.{0}$'.format(
                        sugar.utils.stringutils.to_unicode(ext).lstrip('.')
                    )
                    re.match(
                        pattern,
                        sugar.utils.stringutils.to_unicode(exe),
                        re.I).groups()
                    return True
                except AttributeError:
                    continue
            return False

        # Enhance POSIX path for the reliability at some environments, when $PATH is changing
        # This also keeps order, where 'first came, first win' for cases to find optional alternatives
        system_path = sugar.utils.stringutils.to_unicode(os.environ.get('PATH', ''))
        search_path = system_path.split(os.pathsep)
        if not sugar.utils.platform.is_windows():
            search_path.extend([
                x for x in ('/bin', '/sbin', '/usr/bin',
                            '/usr/sbin', '/usr/local/bin')
                if x not in search_path
            ])

        for path in search_path:
            full_path = os.path.join(path, exe)
            if _is_executable_file_or_link(full_path):
                return full_path
            elif sugar.utils.platform.is_windows() and not _exe_has_ext():
                # On Windows, check for any extensions in PATHEXT.
                # Allows both 'cmd' and 'cmd.exe' to be matched.
                for ext in ext_list:
                    # Windows filesystem is case insensitive so we
                    # safely rely on that behavior
                    if _is_executable_file_or_link(full_path + ext):
                        return full_path + ext
        log.debug("'%s' could not be found in the following search path: '%s'" % (exe, search_path))
    else:
        log.error("No executable was passed to be searched by sugar.utils.path.which()")

    return None


def which_bin(exes):
    """
    Scan over some possible executables and return the first one that is found
    """
    if not isinstance(exes, collections.Iterable):
        return None
    for exe in exes:
        path = which(exe)
        if not path:
            continue
        return path
    return None
