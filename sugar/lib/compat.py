"""
Compatibility between Python2 and Python3
"""

#pylint: disable=E0401,W0611

from sugar.lib import six

if six.PY2:
    import Queue as queue
    from collections import Mapping as CollectionsMapping
else:
    import queue
    from collections.abc import Mapping as CollectionsMapping
