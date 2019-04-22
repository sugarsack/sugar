# coding: utf-8
"""
Entities to be saved in the database.
"""
import datetime
from pony import orm
from sugar.utils.db import database, SerialisableEntity, JobDefaults, ResultDefault


class Host(database.Entity, SerialisableEntity):
    """
    Host object.
    """
    osid = orm.Required(str, unique=True)         # machine ID
    fqdn = orm.Required(str)                      # fqdn
    ipv4 = orm.Optional(str, nullable=True,
                        default=None)             # Primary IPv4 address
    ipv6 = orm.Optional(str, nullable=True,
                        default=None)             # Primary IPv6 address


class Job(database.Entity, SerialisableEntity):
    """
    Job object.
    """
    jid = orm.Required(str)
    created = orm.Required(datetime.datetime, default=datetime.datetime.now())
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    status = orm.Required(str, default=JobDefaults.S_ISSUED)
    query = orm.Required(str)
    tag = orm.Optional(str, nullable=True)        # Tag/label of the job for better search for it
    results = orm.Set("Result")                   # Set of tasks per host. Job ID is the same across the set of hosts.
    args = orm.Optional(str, nullable=True, default=None)
    uri = orm.Required(str)
    env = orm.Required(str)                       # Environment
    kind = orm.Required(int)                      # kind
    type = orm.Required(str)                      # Type: "runner" or "state"


class Result(database.Entity, SerialisableEntity):
    """
    Results of the client.
    """
    job = orm.Required(Job)
    machineid = orm.Required(str)
    status = orm.Required(int, default=ResultDefault.R_NOT_SET)
    fired = orm.Optional(datetime.datetime, nullable=True, default=None)    # When job is just fired by master
    src = orm.Optional(str)                       # Source of the result (if it is a state)
    tasks = orm.Set("Task")


class Task(database.Entity, SerialisableEntity):
    """
    Task. Contains many calls.
    """
    job = orm.Required(Result)                    # Job object ID in the database, not JID
    idn = orm.Required(str)                       # Task IDN (an id of the task in the compiler, a name)
    finished = orm.Optional(datetime.datetime, nullable=True, default=None)
    calls = orm.Set("Call")
    return_data = orm.Optional(str)               # Answer of the task (module return data)
    src = orm.Optional(str)                       # Source of the task
    log_info = orm.Optional(str)                  # Source of the task
    log_warn = orm.Optional(str)                  # Source of the task
    log_err = orm.Optional(str)                   # Source of the task


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
