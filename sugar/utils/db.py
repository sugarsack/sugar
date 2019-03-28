# coding: utf-8
"""
Database helpers
"""
from pony import orm
from sugar.transport.serialisable import Serialisable


database = orm.Database()  # pylint: disable=C0103


class SerialisableEntity:
    """
    Serialisable entity utils.
    """
    def clone(self):
        """
        Clone itself into the serialisable object.

        :return: Serialisable
        """
        export_obj = Serialisable()
        for attr in self.__class__.__dict__:
            if not attr.startswith('_') and not callable(self.__class__.__dict__[attr]):
                obj = getattr(self, attr)
                if obj is not None:
                    obj = obj.__repr__.__self__
                setattr(export_obj, attr,
                        [item.clone() for item in obj] if obj.__class__.__module__.startswith("pony.orm") else obj)
        return export_obj
