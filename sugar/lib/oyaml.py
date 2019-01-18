# coding: utf-8
"""
Ordered YAML. Allows to keep as-is YAML data in the order.
Copyright (c) 2018 wim glenn
License: MIT
https://github.com/wimglenn/oyaml
"""
import sys
from collections import OrderedDict

import yaml as pyyaml

# pylint: disable=W0614,C0103,W0401,C0413

_items = 'viewitems' if sys.version_info < (3,) else 'items'


def map_representer(dumper, data):
    """
    Mapping object representer.

    :param dumper: YAML dumper
    :param data: data to represent
    :return: represented data
    """
    return dumper.represent_dict(getattr(data, _items)())


def map_constructor(loader, node):
    """
    Constructs a map using OrderedDict.

    :param loader: YAML loader
    :param node: YAML node
    :return: OrderedDictionary data
    """
    loader.flatten_mapping(node)
    return OrderedDict(loader.construct_pairs(node))


if pyyaml.safe_dump is pyyaml.dump:
    # PyYAML v4.1
    SafeDumper = pyyaml.dumper.Dumper
    DangerDumper = pyyaml.dumper.DangerDumper
    SafeLoader = pyyaml.loader.Loader
    DangerLoader = pyyaml.loader.DangerLoader
else:
    SafeDumper = pyyaml.dumper.SafeDumper
    DangerDumper = pyyaml.dumper.Dumper
    SafeLoader = pyyaml.loader.SafeLoader
    DangerLoader = pyyaml.loader.Loader

pyyaml.add_representer(dict, map_representer, Dumper=SafeDumper)
pyyaml.add_representer(OrderedDict, map_representer, Dumper=SafeDumper)
pyyaml.add_representer(dict, map_representer, Dumper=DangerDumper)
pyyaml.add_representer(OrderedDict, map_representer, Dumper=DangerDumper)


if sys.version_info < (3, 7):
    pyyaml.add_constructor('tag:yaml.org,2002:map', map_constructor, Loader=SafeLoader)
    pyyaml.add_constructor('tag:yaml.org,2002:map', map_constructor, Loader=DangerLoader)

del map_constructor, map_representer

# Merge PyYAML namespace for drop-in replacement
from yaml import *  # noqa
