"""
Linux traits implementations
"""
from __future__ import absolute_import, unicode_literals
import os
import sugar.utils.files


def get_machine_id():
    """
    Get machine ID
    :return:
    """
    ret = None
    for loc in [loc for loc in ['/etc/machine-id', '/var/lib/dbus/machine-id'] if os.path.exists(loc)]:
        with sugar.utils.files.fopen(loc) as mfh:
            ret = mfh.read().strip() or None
            if ret:
                break

    return ret
