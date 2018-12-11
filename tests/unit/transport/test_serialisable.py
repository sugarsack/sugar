"""
Test serialisable
"""

from __future__ import absolute_import, unicode_literals, print_function

import pytest
from sugar.transport.serialisable import Serialisable, ObjectGate


@pytest.fixture
def obj_structure():
    obj = {
        'foo': {
            'bar': 'blah',
            '.': None
        },
        '.': None,
        'here': {
            'something': {
                'user': 'data',
                'int': 123,
            },
            '.': None
        }
    }

    return obj


class TestSerialise(object):
    """
    Test object serialisation/dumping.
    """

    def test_load(self, obj_structure):
        """
        Test load data from the serialisation.

        :return:
        """
        d = ObjectGate()
        s = d.load(obj_structure)
        assert ObjectGate(s).dump() == obj_structure

    def test_dump(self, obj_structure):
        """
        Test serialise data.

        :return:
        """
        s = Serialisable()
        s.foo.bar = 'blah'
        s.here.something = {'user': 'data', 'int': 123}

        assert ObjectGate(s).dump() == obj_structure
