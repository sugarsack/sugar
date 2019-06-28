# coding: utf-8
"""
Version manipulation utilities.
"""
import numbers
import sugar.lib.exceptions
from distutils.version import LooseVersion as _LooseVersion


class LooseVersion(_LooseVersion):

    def parse(self, vstring):
        _LooseVersion.parse(self, vstring)
        self._str_version = [str(vp).zfill(8) if isinstance(vp, int) else vp for vp in self.version]

    def _cmp(self, other):
        other = LooseVersion(other)

        string_in_version = False
        for part in self.version + other.version:
            if not isinstance(part, int):
                string_in_version = True
                break

        if string_in_version is False:
            return _LooseVersion._cmp(self, other)

        if self._str_version == other._str_version:
            return 0
        if self._str_version < other._str_version:
            return -1
        if self._str_version > other._str_version:
            return 1


def version_cmp(pkg1, pkg2, ignore_epoch=False):
    '''
    Compares two version strings using salt.utils.versions.LooseVersion. This
    is a fallback for providers which don't have a version comparison utility
    built into them.  Return -1 if version1 < version2, 0 if version1 ==
    version2, and 1 if version1 > version2. Return None if there was a problem
    making the comparison.
    '''
    normalise = lambda x: x.split(':', 1)[-1] if ignore_epoch else x
    pkg1 = normalise(pkg1)
    pkg2 = normalise(pkg2)
    out = 0
    try:
        if LooseVersion(pkg1) < LooseVersion(pkg2):
            out = -1
        elif LooseVersion(pkg1) > LooseVersion(pkg2):
            out = 1
    except Exception as exc:
        raise sugar.lib.exceptions.SugarRuntimeException(exc)

    return out


def compare(ver1='', oper='==', ver2='', cmp_func=None, ignore_epoch=False):
    '''
    Compares two version numbers. Accepts a custom function to perform the
    cmp-style version comparison, otherwise uses version_cmp().
    '''
    cmp_map = {'<': (-1,), '<=': (-1, 0), '==': (0,), '>=': (0, 1), '>': (1,)}

    if oper not in ('!=',) and oper not in cmp_map:
        raise sugar.lib.exceptions.SugarRuntimeException("Invalid operator '{}' for version comparison".format(oper))

    if cmp_func is None:
        cmp_func = version_cmp

    cmp_result = cmp_func(ver1, ver2, ignore_epoch=ignore_epoch)
    if cmp_result is None:
        return False

    # Check if integer/long
    if not isinstance(cmp_result, numbers.Integral):
        raise sugar.lib.exceptions.SugarRuntimeException('The version comparison function '
                                                         'did not return an integer/long.')

    if oper == '!=':
        return cmp_result not in cmp_map['==']
    else:
        # Gracefully handle cmp_result not in (-1, 0, 1).
        if cmp_result < -1:
            cmp_result = -1
        elif cmp_result > 1:
            cmp_result = 1

        return cmp_result in cmp_map[oper]
