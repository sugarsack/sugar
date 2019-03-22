# coding: utf-8
"""
Job storage
"""
import os
import errno
import typing
from sugar.lib.compiler.objtask import StateTask
from sugar.lib.jobstore.database import database
from sugar.lib.jobstore.entities import Job, Task, Call
from pony import orm


class JobStorage:
    """
    Store data in the database.
    """
    def __init__(self, config):
        self._config = config
        self._db_path = None
        self.init()

    def register(self, query: str, clientslist: list, expr: str, tasklist: typing.Tuple[StateTask]) -> None:
        """
        Register a new job.

        :param query: Issued matcher expression during the job state or runner.
        :param clientslist: Result of the matcher query
        :param expr: Expression of the job: either it is the name of the state or function etc. I.e. what was called.
        :param tasklist: list of parsed tasks
        :return:
        """

    def get_by_jid(self, jid) -> Job:
        """
        Get a job by jid.

        :param jid: job id.
        :return: Job object.
        """
        return None

    def get_later_then(self, dt) -> list:
        """
        Get a jobs that are later than specified datetime.

        :param dt: datetime threshold.
        :return: list of Job objects
        """
        return []

    def get_by_tag(self, tag) -> Job:
        """
        Get a job by a tag.

        :param tag: Tag in the job, if job has been tagged.
        :return: Job object.
        """
        return None

    def all(self) -> list:
        """
        Get all existing jobs.

        :return: List of job objects.
        """
        return []

    def expire(self) -> None:
        """
        Swipe over jobs and remove those that already outdated.

        :return:
        """

    def export(self, jid, path) -> None:
        """
        Export job to some tar archive.

        :param jid: job id
        :param path: path on the server to dump all the job data into an archive.
        :return: None
        """

    def flush(self) -> None:
        """
        Flush the entire database of all jobs history, state and progress.

        :return: None
        """
        if self._db_path is not None:
            try:
                os.unlink(self._db_path)
            except IOError as exc:
                if exc.errno == errno.ENOENT:
                    pass
            self.init()

    def init(self):
        """
        Initialise database.

        :return:
        """
        database.bind(provider="sqlite", filename=self._db_path, create_db=True)
        database.generate_mapping(create_tables=True)
    def close(self):
        """
        Close and detach database.

        :return:
        """
        database.disconnect()
        database.provider = None
        database.schema = None
