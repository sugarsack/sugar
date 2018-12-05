# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals
from sugar.lib.schema import Schema, And, Use, Optional, SchemaError


client = Schema({
    'master': And(Use(str)),
    Optional('cluster'): [{
        And(Use(str)): {
            Optional('data_port', default=5505): int,
            Optional('ctrl_port', default=5506): int,
        },
    }]
})

master = Schema({

})
