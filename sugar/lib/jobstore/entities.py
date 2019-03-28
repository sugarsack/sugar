# coding: utf-8
"""
Entities to be saved in the database.
"""
import datetime
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
    tag = orm.Optional(str, nullable=True)        # Tag/label of the job for better search for it
    results = orm.Set("Result")                   # Set of tasks per host. Job ID is the same across the set of hosts.


class Result(database.Entity, SerialisableEntity):
    """
    Results of the client.
    """
    R_NOT_SET = 0                                 # N/A. Not available yet
    R_FAULTY = 1                                  # Faulty. Less than 20% machines failed
    R_UNCLEAN = 2                                 # Unclean. At least one machine has warnings
    R_OOPS = 3                                    # Fatal. All machines failed (100%).
    R_DIRTY = 4                                   # Dirty. Most machines with warnings

    job = orm.Required(Job)
    hostname = orm.Required(str)
    status = orm.Required(int, default=R_NOT_SET)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    started = orm.Optional(datetime.datetime, nullable=True, default=None)  # When client picks up the job
    fired = orm.Optional(datetime.datetime, nullable=True, default=None)    # When job is just fired by master
    src = orm.Optional(str)                       # Source of the task
    answer = orm.Optional(str)                    # Answer of the task (module return data)
    log = orm.Optional(str)                       # Log slice during the task performance
    tasks = orm.Set("Task")


class Task(database.Entity, SerialisableEntity):
    """
    Task. Contains many calls.
    """
    job = orm.Required(Result)                    # Job object ID in the database, not JID
    idn = orm.Required(str)                       # Task IDN (an id of the task in the compiler, a name)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    calls = orm.Set("Call")


class Call(database.Entity, SerialisableEntity):
    """
    Function call. Name of the module (uri) and the function.
    """
    task = orm.Required(Task)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    uri = orm.Required(str)                       # URI of the module/function
    src = orm.Optional(str)                       # Source of the call in YAML (params etc)
    errcode = orm.Optional(int)                   # Error code
    output = orm.Optional(str)                    # JSON results
