# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals
from sugar.lib.schemelib import Schema, And, Use, Optional, SchemaError

# Client configuration scheme
client_scheme = Schema({
    And('master'): [
        {
            Optional('hostname', default='sugar'): str,
            Optional('data_port', default=5505): int,
            Optional('ctrl_port', default=5506): int,
        },
    ],
    And('log'): [
        {
            And('file'): str,
            Optional('level'): str,
            Optional('rotate'): int,
            Optional('max_size_mb'): int,
        }
    ]
})

# Master configuration scheme
master_scheme = Schema({

})
