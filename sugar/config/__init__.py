# coding=utf-8

from __future__ import absolute_import, print_function, unicode_literals

import copy
import yaml
import os
import logging

from sugar.utils.structs import merge_dicts, ImmutableDict, dict_to_object, merge_missing
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.config import scheme

log = logging.getLogger(__name__)


class _DefaultConfigurations(object):
    """
    This class is a structure for the
    default configurations on all components.
    """

    # Default master configuration
    # NOTE: Defaults of this are merged to the config,
    # if they do not exist there.
    master = {
    }

    # Default client configuration.
    # NOTE: Defaults of this are merged to the config,
    # if they do not exist there.
    client = {
        'master': [
            {
                'hostname': 'sugar',
                'ctrl_port': 5505,
                'data_port': 5506,
            },
        ]
    }

    @staticmethod
    def add_defaults(config):
        """
        Go over each aggregate and ensure record has defaults updated.

        :return:
        """
        for method in _DefaultConfigurations.__dict__:
            if method.startswith('{}__default_'.format(_DefaultConfigurations.__name__)):
                getattr(_DefaultConfigurations, method)(config)

    # Methods below are fixtures. They take corresponding chunk
    # from the default config above, iterate over real life config
    # and add defaults.
    #
    # To add a fixture:
    #   1. Create a method with "__default_" prefix
    #   2. Add one parameter that takes life conf data.

    @staticmethod
    def __default_c_master_ports(config):
        """
        Update ctrl/data ports on the client.

        :return:
        """
        for target in config['master']:
            merge_missing(target, _DefaultConfigurations.client['master'][0])


@Singleton
class CurrentConfiguration(object):
    """
    Reads the current configuration of the running component
    and keeps it in a singleton.

    This data is shared via socket to the controlling client
    instead of instantiating it again from the disk.
    """

    DEFAULT_PATH = '/etc/sugar'

    def __init__(self, altpath):
        """
        Load configurations.
        Order:
          1. Default or specified
          2. Custom in user home

        :param altpath: alternative location of the configuration path
        """
        self.component = get_current_component()
        self.__config = copy.deepcopy(getattr(_DefaultConfigurations, self.component))
        if self.component and self.component != 'local':
            for path in [altpath or self.DEFAULT_PATH, os.path.expanduser('~')]:
                self._load_config(os.path.join(path, '{}.conf'.format(self.component)))

    def _load_config(self, config_path):
        '''
        Load configuration of the specific path.

        :param target:
        :return:
        '''
        if config_path and os.path.isfile(config_path):
            with open(config_path) as cfg_fh:
                self.__merge(yaml.load(cfg_fh.read()))

    def __merge(self, conf):
        """
        Merge another piece of config.

        :param conf:
        :return:
        """
        merge_dicts(self.__config, conf)
        getattr(scheme, '{}_scheme'.format(self.component)).validate(self.__config)
        _DefaultConfigurations.add_defaults(self.__config)

    def update(self, data):
        """
        Bulk-update the entire configuration.

        :param data:
        :return:
        """
        self.__merge(data)

    @property
    def root(self):
        """
        Get root of the configuration
        :return:
        """
        return dict_to_object(ImmutableDict(self.__config))


def get_config(altpath=None):
    """
    Get current config.
    Parameter altpath is only considered at first init time.

    :param altpath: Alternative path
    :return:
    """
    return CurrentConfiguration(altpath=altpath).root
