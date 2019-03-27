# coding: utf-8
"""
Job storage
"""
import os
import errno
import json
import datetime
import typing
import tarfile
import io

from pony import orm

from sugar.lib.compiler.objtask import StateTask
from sugar.lib.jobstore.entities import Job
from sugar.lib.jobstore.stats import JobStats
from sugar.lib.jobstore.components import ResultDict
from sugar.utils.db import database
from sugar.utils.sanitisers import join_path
from sugar.utils.jid import jidstore
from sugar.lib.compat import yaml
import sugar.utils.exitcodes
import sugar.lib.exceptions

# pylint: disable=R0201


class JobStorage:
    """
    Store data in the database.
    """
    def __init__(self, config, path=None):
        self._config = config
        self._db_path = self._config.cache.path if path is None else path
        self.init()

    def new(self, query: str, clientslist: list, expr: str, tag: str = None) -> str:
        """
        Register a new job.

        :param query: Issued matcher expression during the job state or runner.
        :param clientslist: Result of the matcher query
        :param expr: Expression of the job: either it is the name of the state or function etc. I.e. what was called.
        :param tag: Tag (label) of the job.
        :return: jid (new job id)
        """
        jid = jidstore.create()
        with orm.db_session:
            job = Job(jid=jid, query=query, expr=expr, created=datetime.datetime.now(), tag=tag)
            for hostname in clientslist:
                job.results.create(hostname=hostname)
        return jid

    def add_tasks(self, jid: str, *tasks: StateTask, hostname: str = None, src: str = None) -> None:
        """
        Adds a completed task to the job per a hostname.

        :param jid: job ID
        :param tasks: List of tasks that has been completed
        :raises SugarJobStoreException: if hostname or machine ID was not specified.
        :return: None
        """
        if hostname is None:
            raise sugar.lib.exceptions.SugarJobStoreException("Hostname or machine ID is required")

        with orm.db_session:
            job = Job.get(jid=jid)
            for result in job.results.select(lambda result: result.hostname == hostname):
                result.src = src
                for task in tasks:
                    _task = result.tasks.create(idn=task.idn)
                    for call in task.calls:
                        _task.calls.create(uri=call.uri, src=call.src)

    def report_job(self, jid: str, hostname: str, src: str, log: str, answer: str) -> None:
        """
        Report compiled job source on the client.

        :param jid: Job id
        :param hostname: hostname
        :param src: source of the job (YAML)
        :param log: text of the log snipped
        :param answer: the entire (compiled) answer of the job
        :return: None
        """
        if src is not None or log is not None or answer is not None:
            with orm.db_session:
                result = Job.get(jid=jid).results.select(lambda result: result.hostname == hostname).first()
                if src is not None:
                    result.src = src
                if log is not None:
                    result.log = log
                if answer is not None:
                    result.answer = answer

    def report_call(self, jid: str, hostname: str, idn: str,
                    uri: str, errcode: int, output: str, finished: datetime) -> None:
        """
        Report job progress. Each time task is completed with any kind of result,
        this should update current status of it.

        :param jid: Job ID
        :param idn: Identificator of the task
        :param uri: URI of the called function
        :param errcode: return code of the performed function
        :param output: output of the function
        :param hostname: hostname of the machine that reports this call
        :param finished: date/time when call has been finished
        :raises SugarJobStoreException: if 'output' parameter is not a JSON string
        :return: None
        """
        with orm.db_session:
            result = Job.get(jid=jid).results.select(lambda result: result.hostname == hostname).first()
            for task in result.tasks.select(lambda task: task.idn == idn):
                for call in task.calls.select(lambda call: call.uri == uri):
                    if not isinstance(output, str):
                        raise sugar.lib.exceptions.SugarJobStoreException("output expected to be a JSON string")
                    try:
                        json.loads(output)
                    except Exception as exc:
                        raise sugar.lib.exceptions.SugarJobStoreException(exc)
                    call.output = output
                    call.errcode = errcode
                    call.finished = finished

    def get_done_stats(self, jid: str) -> JobStats:
        """
        Get status of done.

        :param jid: Job ID.
        :return: stats object
        """
        job = self.get_by_jid(jid)
        tasks = 0
        for result in job.results:
            _tasks = len(result.tasks)
            if _tasks > tasks:
                tasks = _tasks
        tasks = tasks * len(job.results)
        stats = JobStats(jid=jid, tasks=tasks)
        with orm.db_session:
            finished = orm.select(job for job in Job if job.jid == jid
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.finished is not None)
            stats.finished = len(finished)
        return stats

    def get_by_jid(self, jid: str) -> Job:
        """
        Get a job by jid.

        :param jid: job id.
        :return: Job object.
        """
        with orm.db_session:
            job = Job.get(jid=jid)
            if job is not None:
                job.clone()
        return job

    def get_later_then(self, dtm: datetime) -> list:
        """
        Get a jobs that are later than specified datetime.

        :param dtm: datetime threshold.
        :return: list of Job objects
        """
        with orm.db_session:
            return [job.clone() for job in orm.select(job for job in Job if job.created > dtm)]

    def get_not_finished(self) -> list:
        """
        Get unfinished jobs.

        :return: list of unfinished jobs, where calls are not yet reported
        """
        jobs = []
        with orm.db_session:
            for job in orm.select(job for job in Job
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.finished is None):
                jobs.append(job.clone())
        return jobs

    def get_finished(self) -> list:
        """
        Get finished jobs.

        :return: list of finished jobs, where calls are reported already
        """
        jobs = []
        with orm.db_session:
            for job in orm.select(job for job in Job
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.finished is not None):
                jobs.append(job.clone())
        return jobs

    def get_failed(self) -> list:
        """
        Get any job that has at least one failed call.

        :return: list of failed jobs
        """
        jobs = []
        with orm.db_session:
            for job in orm.select(job for job in Job
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.errcode != sugar.utils.exitcodes.EX_OK):
                jobs.append(job.clone())
        return jobs

    def get_suceeded(self) -> list:
        """
        Get jobs that has no single failure inside.

        :return: list of succeeded jobs
        """
        jobs = []
        with orm.db_session:
            for job in orm.select(job for job in Job
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.errcode == sugar.utils.exitcodes.EX_OK):
                jobs.append(job.clone())
        return jobs

    def get_by_tag(self, tag) -> typing.List[Job]:
        """
        Get a job by a tag.

        :param tag: Tag in the job, if job has been tagged.
        :return: Job object.
        """
        with orm.db_session:
            return [job.clone() for job in orm.select(job for job in Job if job.tag == tag)]

    def get_all(self, limit=25, offset=0) -> list:
        """
        Get all existing jobs.

        :param limit: limit of amount of the returned objects.
        :param offset: offset in the database.

        :return: List of job objects.
        """
        if limit is None:
            limit = 0
        if offset is None:
            offset = 0
        with orm.db_session:
            if limit + offset:
                result = [job.clone() for job in orm.select(
                    job for job in Job).limit(limit, offset=offset)]
            else:
                result = [job.clone() for job in orm.select(job for job in Job)]
        return result

    def expire(self, dtm=None) -> None:
        """
        Swipe over jobs and remove those that already outdated.

        :param dtm: date/time threshold (default last five days)
        :return: None
        """
        with orm.db_session:
            orm.delete(job for job in Job if job.created < dtm)

    def delete_by_jid(self, jid: str) -> None:
        """
        Delete a particular job by JID.

        :param jid: string job id
        :return: None
        """
        if jid is not None:
            with orm.db_session:
                orm.delete(job for job in Job if job.jid == jid)

    def delete_by_tag(self, tag: str) -> None:
        """
        Delete a particular job by tag

        :param tag: string tag
        :return: None
        """
        if tag is not None:
            with orm.db_session:
                orm.delete(job for job in Job if job.tag == tag)

    def export(self, jid, path) -> None:
        """
        Export job to some tar archive.

        :param jid: job id
        :param path: path on the server to dump all the job data into an archive.
        :raises SugarJobStoreException: if an archive file already exists
        :return: None
        """
        # pylint: disable=R0914
        os.makedirs(path, exist_ok=True)
        path = "{}/sugar-job-{}.tar.gz".format(path, jid)

        # This should not happen, but still.
        if os.path.exists(path):
            raise sugar.lib.exceptions.SugarJobStoreException("File '{}' already exists".format(path))

        archive = tarfile.open(path, mode="w:gz")
        data = []
        with orm.db_session:
            job = Job.get(jid=jid)

            job_data = ResultDict()
            job_data["jid"] = job.jid
            job_data["created"] = job.created
            job_data["finished"] = job.finished
            job_data["status"] = job.status
            job_data["query"] = job.query
            job_data["identifier"] = job.expr
            job_data["tag"] = job.tag

            data.append(("job-info.yaml", job_data, False))

            for result in job.results:
                result_data = ResultDict()
                result_data["status"] = result.status
                result_data["finished"] = result.finished
                result_data["tasks"] = []

                for task in result.tasks:
                    task_data = ResultDict()
                    task_data["identifier"] = task.idn
                    task_data["finished"] = task.finished
                    task_data["calls"] = []

                    for call in task.calls:
                        call_data = ResultDict()
                        call_data["finished"] = call.finished
                        call_data["URI"] = call.uri
                        call_data["errcode"] = call.errcode
                        call_data["output"] = call.output

                        task_data["calls"].append(call_data)
                        if call.src:
                            data.append(("{}/src-{}.{}.yaml".format(result.hostname, task.idn, call.uri), call.src, True))
                    result_data["tasks"].append(task_data)

                data.append(("{}/result.yaml".format(result.hostname), result_data.to_dict(), False))
                data.append(("{}/source.yaml".format(result.hostname), result.src, True))
                if result.answer:
                    data.append(("{}/answer.yaml".format(result.hostname), result.answer, True))
                if result.log:
                    data.append(("{}/client.log".format(result.hostname), result.log, True))

        for d_name, d_content, as_is in data:
            body = yaml.dump(d_content, default_flow_style=False) if not as_is else d_content
            src = io.BytesIO()
            src.write(body.encode("utf-8"))
            src.seek(0)
            info = tarfile.TarInfo(name=d_name)
            info.size = len(body)
            archive.addfile(info, src)
        # pylint: enable=R0914

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
        self._db_path = join_path(self._db_path, "/master/jobs.data")
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        database.bind(provider="sqlite", filename=self._db_path, create_db=True)
        database.generate_mapping(create_tables=True)

    def close(self) -> None:
        """
        Close and detach database.

        :return: None
        """
        database.disconnect()
        database.provider = None
        database.schema = None
