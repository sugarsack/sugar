# coding=utf-8
import copy
import yaml
import os
from sugar.utils.structs import merge_dicts, dict_to_object

DEFAULT_SHELL_CONFIG = {
    'debug': False,

    'listener': {
        'http_port': 8080,
        'ssl_port': 8433.
    },

    'log': {
        'file': '',
        'console': True,
        'level': 'all',  # all, debug, error, fatal, critical, warning
    },

    'ssl': {
        'activated': False,
        'certificates': '',
        'key_file': '',
        'certificate_file': '',
    },
}


def load_configuration(config_path):
    '''
    Load configuration

    :param target:
    :return:
    '''
    base = copy.deepcopy(DEFAULT_SHELL_CONFIG)
    if config_path and os.path.isfile(config_path):
        with open(config_path) as cfg_fh:
            conf = yaml.load(cfg_fh.read())
    else:
        conf = {}
    merge_dicts(base, conf)

    return dict_to_object(base)
