# coding: utf-8
"""
Database helpers
"""
from pony import orm
from sugar.transport.serialisable import Serialisable


database = orm.Database()  # pylint: disable=C0103


class JobDefaults:
    """
    Job defaults.
    """
    S_ISSUED = "Pending"                          # not a single machine yet got this
    S_IN_PROGRESS = "Running"                     # at least one machine got it
    S_FINISHED = "Finished"                       # all machines returned results


class ResultDefault:
    """
    Results defaults.
    """
    R_NOT_SET = 0                                 # N/A. Not available yet
    R_FAULTY = 1                                  # Faulty. Less than 20% machines failed
    R_UNCLEAN = 2                                 # Unclean. At least one machine has warnings
    R_OOPS = 3                                    # Fatal. All machines failed (100%).
    R_DIRTY = 4                                   # Dirty. Most machines with warnings


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
