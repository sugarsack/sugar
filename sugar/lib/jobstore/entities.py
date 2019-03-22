# coding: utf-8
"""
Entities to be saved in the database.
"""
import datetime
import inspect
from pony import orm
from sugar.utils.db import database, SerialisableEntity


class Job(database.Entity, SerialisableEntity):
    """
    Job object.
    """
    # Job state
    S_ISSUED = "Pending"                          # not a single machine yet got this
    S_IN_PROGRESS = "Running"                     # at least one machine got it
    S_FINISHED = "Finished"                       # all machines returned results

    jid = orm.Required(str)
    created = orm.Required(datetime.datetime, default=datetime.datetime.now())
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    status = orm.Required(str, default=S_ISSUED)

    query = orm.Required(str)
    expr = orm.Required(str)                      # job expression (state name or function name)

    tag = orm.Optional(str)                       # Tag/label of the job for better search for it
    tasks = orm.Set("Task")


class Task(database.Entity, SerialisableEntity):
    """
    Task. Contains many calls.
    """
    job = orm.Required(Job)                       # Job object ID in the database, not JID
    idn = orm.Required(str, unique=True)          # Task IDN (an id of the task in the compiler, a name)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    calls = orm.Set("Call")
    results = orm.Set("Result")


class Result(database.Entity, SerialisableEntity):
    """
    Results of the client.
    """
    R_NOT_SET = "N/A"                             # Not available yet
    R_FAULTY = "Faulty"                           # less than 20% machines failed
    R_UNCLEAN = "Unclean"                         # at least one machine has warnings
    R_OOPS = "Oops"                               # all machines failed (100%). Did you just made a joke? :-)
    R_DIRTY = "Dirty"                             # Most machines with warnings

    job = orm.Required(Task)
    hostname = orm.Required(str)
    status = orm.Required(str, default=R_NOT_SET)

    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    src = orm.Optional(str)                       # Source of the task
    answer = orm.Optional(str)                    # Answer of the task (module return data)
    log = orm.Optional(str)                       # Log slice during the task performance


class Call(database.Entity, SerialisableEntity):
    """
    Function call. Name of the module (uri) and the function.
    """
    task = orm.Required(Task)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    uri = orm.Required(str)                       # URI of the module/function
    src = orm.Optional(str)                       # Source of the call in YAML (params etc)
