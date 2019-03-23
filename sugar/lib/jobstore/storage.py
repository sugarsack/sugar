# coding: utf-8
"""
Job storage
"""
import os
import errno
import json
from sugar.lib.compiler.objtask import StateTask
from sugar.lib.jobstore.entities import Job, Task, Call
from sugar.lib.jobstore.stats import JobStats
from sugar.utils.db import database
from sugar.utils.sanitisers import join_path
from sugar.utils.jid import jidstore
import sugar.lib.exceptions
from pony import orm


class JobStorage:
    """
    Store data in the database.
    """
    def __init__(self, config):
        self._config = config
        self._db_path = None
        self.init()

    def new(self, query: str, clientslist: list, expr: str) -> str:
        """
        Register a new job.

        :param query: Issued matcher expression during the job state or runner.
        :param clientslist: Result of the matcher query
        :param expr: Expression of the job: either it is the name of the state or function etc. I.e. what was called.
        :return: jid (new job id)
        """
        jid = jidstore.create()
        with orm.db_session:
            job = Job(jid=jid, query=query, expr=expr)
            for hostname in clientslist:
                job.results.create(hostname=hostname)
        return jid

    def add_tasks(self, jid, *tasks: StateTask, job_src: str = None) -> None:
        """
        Adds a completed task to the job.

        :param jid: job ID
        :param tasks: List of tasks that has been completed
        :param src: Job source
        :return: None
        """
        with orm.db_session:
            job = Job.get(jid=jid)

            if job_src is not None:
                job.src = job_src

            for task in tasks:
                _task = job.tasks.create(idn=task.idn)
                for call in task.calls:
                    _task.calls.create(uri=call.uri, src=call.src)

    def report_call(self, jid, idn, uri, errcode, output) -> None:
        """
        Report job progress. Each time task is completed with any kind of result,
        this should update current status of it.

        :param jid: Job ID
        :param idn: Identificator of the task
        :param uri: URI of the called function
        :param errcode: return code of the performed function
        :param output: output of the function
        :return: None
        """
        with orm.db_session:
            job = Job.get(jid=jid)
            for task in job.tasks.select(lambda task: task.idn == idn):
                print(task)
                for call in task.calls.select(lambda call: call.uri == uri):
                    if not isinstance(output, str):
                        raise sugar.lib.exceptions.SugarJobStoreException("output expected to be a JSON string")
                    try:
                        json.loads(output)
                    except Exception as exc:
                        raise sugar.lib.exceptions.SugarJobStoreException(exc)
                    call.output = output
                    call.errcode = errcode

    def get_done_stats(self):
        """
        Get status of done.

        :return:
        """
        stats = JobStats()
        return stats

    def get_by_jid(self, jid) -> Job:
        """
        Get a job by jid.

        :param jid: job id.
        :return: Job object.
        """
        with orm.db_session:
            job = Job.get(jid=jid)
            job.clone()
        return job

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

    def all(self, limit=25, offset=0) -> list:
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

    def init(self) -> None:
        """
        Initialise database.

        :return: None
        """
        self._db_path = join_path(self._config.cache.path, "/master/jobs.data")
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
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
