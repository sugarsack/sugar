# coding: utf-8
"""
Configuration scheme for validation.
"""

from __future__ import absolute_import, print_function, unicode_literals

import copy

from sugar.utils.structs import merge_dicts
from sugar.lib.schemelib import Schema, And, Optional


class SchemeBuilder(object):
    """
    Scheme builder.
    """

    # Common configuration scheme for validation.
    # This gets merged to anything else.
    # Expand it here.
    __common_scheme = {
        And('log'): [
            {
                And('file'): str,
                Optional('level'): str,
                Optional('rotate'): int,
                Optional('max_size_mb'): int,
            }
        ],
        And('cache'): {
            And('path'): str,
        },
    }

    # Client configuration scheme for validation
    # Expand it here
    __client_scheme = {
        And('master'): [
            {
                Optional('hostname', default='sugar'): str,
                Optional('data_port', default=5505): int,
                Optional('ctrl_port', default=5506): int,
            },
        ],
    }

    # Master configuration scheme for validation
    # Expand it here
    __master_scheme = {
        Optional('crypto'): {
            Optional('ssl'): {
                Optional('certificate', default="certificate.pem"): str,
                Optional('private', default="private_key.pem"): str,
                Optional('verify', default="true"): bool,
            },
        },
        Optional('terminal'): {
            Optional('colors'): int,
            Optional('encoding'): str,
        }
    }

    def get_master_scheme(self):
        """
        Get master configuration scheme.

        :return: Schema object
        """
        return self.__merge_scheme(self.__master_scheme)

    def get_client_scheme(self):
        """
        Get client configuration scheme

        :return: Schema object
        """
        return self.__merge_scheme(self.__client_scheme)

    def __merge_scheme(self, target):
        """
        Merge target scheme.

        :param target:
        :return: Schema object
        """
        target = copy.deepcopy(target)
        merge_dicts(target, self.__common_scheme)

        return Schema(target)


# pylint: disable=C0103
# Client configuration scheme
client_scheme = SchemeBuilder().get_client_scheme()

# Master configuration scheme
master_scheme = SchemeBuilder().get_master_scheme()
# pylint: enable=C0103
