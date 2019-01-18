"""
Compatibility between Python2 and Python3
"""

# pylint: disable=E0401,W0611,C0412

from sugar.lib import six

if six.PY2:
    import Queue as queue
    from collections import Mapping as CollectionsMapping
else:
    import queue
    from collections.abc import Mapping as CollectionsMapping

# Ordered YAML
from yaml import scanner
from sugar.lib import oyaml as yaml
yaml.scanner = scanner
del scanner
