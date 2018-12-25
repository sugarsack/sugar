"""
Compatibility between Python2 and Python3
"""

from sugar.lib import six

if six.PY2:
    import Queue as queue
else:
    import queue
