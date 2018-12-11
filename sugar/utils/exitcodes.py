# coding: utf-8
'''
Classification of Sugar exit codes.  These are intended to augment
universal exit codes (found in Python's `os` module with the `EX_`
prefix or in `sysexits.h`).
'''

# The os.EX_* exit codes are Unix only so in the interest of cross-platform
# compatiblility define them explicitly here.
#
# These constants are documented here:
# https://docs.python.org/2/library/os.html#os.EX_OK

EX_OK = 0                 # successful termination
EX_GENERIC = 1            # Generic
EX_USAGE = 64             # command line usage error
EX_NOUSER = 67            # addressee unknown
EX_UNAVAILABLE = 69       # service unavailable
EX_SOFTWARE = 70          # internal software error
EX_CANTCREAT = 73         # can't create (user) output file
EX_TEMPFAIL = 75          # temp failure; user is invited to retry
EX_NOPERM = 77            # permission denied

