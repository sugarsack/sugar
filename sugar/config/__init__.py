# coding=utf-8
"""
Configuration handler.
This keeps configuration schema, validation and singleton to pick
it up from every point of project code at any time without re-reading
the whole thing from the disk.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import copy
import yaml

from sugar.utils.structs import merge_dicts, ImmutableDict, dict_to_object, merge_missing
from sugar.utils.objects import Singleton
from sugar.utils.cli import get_current_component
from sugar.config import scheme


class _DefaultConfigurations(object):
    """
    This class is a structure for the
    default configurations on all components.
    """

    # Default common configuration for all components
    # This is inherited as is at its main level.
    # Common part should be designed at the top levels.
    _common = {
        # TODO: Get rid of this list!
        'log': [
            {
                'file': 'STDOUT',
                'level': 'debug',
                'rotate': 10,
                'max_size_mb': 10,
            }
        ]
    }

    # Default master configuration
    # NOTE: Defaults of this are merged to the config,
    # if they do not exist there.
    _master = {
        'crypto': {
            'ssl': {
                'certificate': 'certificate.pem',
                'private': 'private_key.pem',
            },
        },
        'terminal': {
            'colors': 16,
            'encoding': 'ascii',
        }
    }

# Default client configuration.
    # NOTE: Defaults of this are merged to the config,
    # if they do not exist there.
    _client = {
        'master': [
            {
                'hostname': 'sugar',
                'ctrl_port': 5505,
                'data_port': 5506,
            },
        ],
    }

    @staticmethod
    def master():
        """
        Get master default configuration

        :return: dict
        """
        return _DefaultConfigurations._get_config(_DefaultConfigurations._master)

    @staticmethod
    def client():
        """
        Get master default configuration

        :return: dict
        """
        return _DefaultConfigurations._get_config(_DefaultConfigurations._client)

    @staticmethod
    def _get_config(config):
        """
        Mix dictionaries.

        :return: dict
        """
        config = copy.deepcopy(config)
        merge_dicts(config, _DefaultConfigurations._common)

        return config

    @staticmethod
    def add_defaults(config, opts):
        """
        Go over each aggregate and ensure record has defaults updated.

        :param config: configuration dictionary
        :param opts: overlay for the configuration
        :return: None
        """
        for method in _DefaultConfigurations.__dict__:
            if method.startswith('{}__default_{}_'.format(_DefaultConfigurations.__name__, get_current_component())):
                getattr(_DefaultConfigurations, method)(config, opts)

    # Methods below are fixtures. They take corresponding chunk
    # from the default config above, iterate over real life config
    # and add defaults.
    #
    # To add a fixture:
    #   1. Create a static method with "__default_[T]_" prefix, where T is component, e.g. "client", or "master" etc.
    #   2. Add parameter: takes life conf data and command line opts to override them.

    @staticmethod
    def __default_client_master_ports(config, opts):  # pylint: disable=W0613
        """
        Update ctrl/data ports on the client.

        :param config: configuration
        :param opts: config overlay
        :return: None
        """
        for target in config['master']:
            merge_missing(target, _DefaultConfigurations.client()['master'][0])

    @staticmethod
    def ___reset_logging_level(config, opts):
        """
        Roll over the config and update logging levels.

        :param config: configuration
        :param opts: config overlay
        :return: None
        """
        for target in config['log']:
            merge_missing(target, _DefaultConfigurations.client()['log'][0])
            if opts and opts.log_level is not None:
                target['level'] = opts.log_level

    __default_master_reset_logging_level = __default_client_reset_logging_level = ___reset_logging_level


@Singleton
class CurrentConfiguration(object):
    """
    Reads the current configuration of the running component
    and keeps it in a singleton.

    This data is shared via socket to the controlling client
    instead of instantiating it again from the disk.
    """

    DEFAULT_PATH = '/etc/sugar'
    HOME_PATH = "{}/.sugar"

    def __init__(self, altpath, opts):
        """
        Load configurations.
        Order:
          1. Default or specified
          2. Custom in user home

        :param altpath: alternative location of the configuration path
        """
        self.component = get_current_component()
        self.__config = copy.deepcopy(getattr(_DefaultConfigurations, self.component)())
        self.__opts = opts
        if self.component and self.component != 'local':
            for path in [altpath, self.HOME_PATH.format(os.path.expanduser("~")), self.DEFAULT_PATH]:
                if not path:
                    continue
                cfg_file = os.path.join(path, '{}.conf'.format(self.component))
                if os.path.isdir(path):
                    self._load_config(cfg_file)
                    self.__config['config_path'] = path
                    break

    def _load_config(self, config_path):
        """
        Load configuration of the specific path.

        :param config_path: configuration path
        :return: None
        """
        if config_path and os.path.isfile(config_path):
            with open(config_path) as cfg_fh:
                self.__merge(yaml.load(cfg_fh.read()))

    def __merge(self, conf):
        """
        Merge another piece of config.

        :param conf:
        :return:
        """
        merge_dicts(self.__config, conf or {})
        config_path = self.__config.pop("config_path", None)
        getattr(scheme, '{}_scheme'.format(self.component)).validate(self.__config)
        if config_path is not None:
            self.__config["config_path"] = config_path
        _DefaultConfigurations.add_defaults(self.__config, self.__opts)

    def update(self, data):
        """
        Bulk-update the entire configuration.

        :param data: Configuration
        :return: None
        """
        # TODO: this might flush config on dynamic update. Bug or feature? (TBD)
        # Scenario when this might happen:
        #   1. Configure only what is different from the default configuration, say option A and B.
        #   2. Defaults are merged on top of what is left intact, say option C is from default.
        #   3. Now your config has option A and B custom, while C is default.
        #   4. Update with even less data than in No.1, say only option A.
        #   5. Now your config has option A custom, while B and C default.

        self.__merge(data)

    @property
    def root(self):
        """
        Get root of the configuration

        :return: Object
        """
        return dict_to_object(ImmutableDict(self.__config))


def get_config():
    """
    Get current config.
    Parameter altpath is only considered at first init time.

    :return: Configuration object
    """
    return CurrentConfiguration(None, None).root
