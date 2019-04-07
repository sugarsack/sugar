# coding: utf-8
"""
Job storage
"""
import os
import errno
import json
import pytz
import datetime
import typing
import tarfile
import io

from pony import orm

from sugar.lib.compiler.objtask import StateTask
from sugar.lib.jobstore.entities import Job, Host
from sugar.lib.jobstore.stats import JobStats
from sugar.lib.jobstore.components import ResultDict
from sugar.utils.db import database, JobDefaults
from sugar.utils.sanitisers import join_path
from sugar.utils.jid import jidstore
from sugar.lib.compat import yaml
import sugar.utils.exitcodes
import sugar.lib.exceptions
from sugar.components.server.pdatastore import PDataContainer
# pylint: disable=R0201,R0904


class JobStorage:
    """
    Store data in the database.
    """
    def __init__(self, config, path=None):
        self._config = config
        self._db_path = self._config.cache.path if path is None else path
        self.init()

    def add_host(self, fqdn: str, osid: str, ipv4: str, ipv6: str) -> None:
        """
        Add host to the cache or update if it changes.

        :param fqdn: FQDN hostname
        :param osid: machine ID (systemd or automatically generated)
        :param ipv4: Primary IPv4 address, if any
        :param ipv6: Primary IPv6 address, if any
        :return: None
        """
        with orm.db_session(optimistic=False):
            host = Host.get(osid=osid)
            if host is None:
                Host(fqdn=fqdn, osid=osid, ipv4=ipv4, ipv6=ipv6)
            elif host.fqdn != fqdn or host.ipv4 != ipv4 or host.ipv6 != ipv6:
                host.fqdn = fqdn
                host.ipv4 = ipv4
                host.ipv6 = ipv6

    def get_host(self, fqdn: str = None, osid: str = None, ipv4: str = None, ipv6: str = None, noid: bool = True):
        """
        Get host by any of the criteria.

        :param fqdn: FQDN hostname
        :param osid: machine ID (systemd or automatically generated)
        :param ipv4: Primary IPv4 address, if any
        :param ipv6: Primary IPv6 address, if any
        :param remove record ID from the serialised result
        :return: None
        """
        with orm.db_session(optimistic=False):
            host = None
            for argk, argv in [("fqdn", fqdn), ("osid", osid), ("ipv4", ipv4), ("ipv6", ipv6)]:
                if argv:
                    host = Host.get(**{argk: argv})
            if host is not None:
                host = host.clone()
                if noid:
                    del host.id
            return host

    def new(self, query: str, clientslist: typing.List[PDataContainer],
            expr: str, tag: str = None, jid: str = None) -> str:
        """
        Register a new job.

        :param query: Issued matcher expression during the job state or runner.
        :param clientslist: Result of the matcher query, list of PDataContainer class.
        :param expr: Expression of the job: either it is the name of the state or function etc. I.e. what was called.
        :param tag: Tag (label) of the job.
        :param jid: reuse passed in JID.
        :return: jid (new job id)
        """
        if not clientslist:
            raise sugar.lib.exceptions.SugarJobStoreException("Registering job with no target clients?")

        if jid is None or not jidstore.is_jid(jid):
            jid = jidstore.create()
        with orm.db_session(optimistic=False):
            job = Job(jid=jid, query=query, expr=expr, created=datetime.datetime.now(tz=pytz.UTC), tag=tag)
            for target in clientslist:
                job.results.create(hostname=target.id)
        return jid

    def set_as_fired(self, jid: str, target: PDataContainer) -> None:
        """
        Mark job as "fired". Which means job is not necessary was picked up and accepted.
        But it means that the master fired it over the network.

        :param jid: Job ID
        :param target: client target
        :return: None
        """
        with orm.db_session(optimistic=False):
            for job in orm.select(job for job in Job if job.jid == jid):
                job.status = JobDefaults.S_ISSUED
                for result in job.results:
                    if result.hostname == target.id:
                        result.fired = datetime.datetime.now(tz=pytz.UTC)

    def add_tasks(self, jid: str, *tasks: StateTask, target: PDataContainer = None, src: str = None) -> None:
        """
        Adds a completed tasks to te job per a target (system ID).

        :param jid: job id
        :param tasks: list of tasks
        :param target: machine to add tasks for
        :param src: source of the compiled task on the machine
        :raises SugarJobStoreException: if hostname or machine ID was not specified.
        :return: None
        """
        if target is None:
            raise sugar.lib.exceptions.SugarJobStoreException("Hostname or machine ID is required")

        with orm.db_session(optimistic=False):
            job = Job.get(jid=jid)
            for result in job.results.select(lambda result: result.hostname == target.id):
                result.src = src
                for task in tasks:
                    _task = result.tasks.create(idn=task.idn)
                    for call in task.calls:
                        _task.calls.create(uri=call.uri, src=call.src)

    def report_job(self, jid: str, target: PDataContainer, src: str, answer: str, uri: str = None) -> None:
        """
        Report compiled job source on the client.

        :param jid: Job id
        :param target: target machine
        :param src: source of the job (YAML)
        :param answer: the entire (compiled) answer of the job
        :param uri: URI from the state. Otherwise None, which is a fallback of job.expr
        :return: None
        """
        if src is not None or answer is not None:
            with orm.db_session(optimistic=False):
                job = Job.get(jid=jid)
                result = job.results.select(lambda result: result.hostname == target.id).first()
                task = result.tasks.create(idn=uri or job.expr)
                if src is not None:
                    task.src = src
                if answer is not None:
                    task.answer = answer
                    job.status = JobDefaults.S_FINISHED

    def report_call(self, jid: str, target: PDataContainer, idn: str,
                    uri: str, errcode: int, output: str, finished: datetime) -> None:
        """
        Report job progress. Each time task is completed with any kind of result,
        this should update current status of it.

        :param jid: Job ID
        :param idn: Identificator of the task
        :param uri: URI of the called function
        :param errcode: return code of the performed function
        :param output: output of the function
        :param target: machine that reports this call
        :param finished: date/time when call has been finished
        :raises SugarJobStoreException: if 'output' parameter is not a JSON string
        :return: None
        """
        with orm.db_session(optimistic=False):
            job = Job.get(jid=jid)
            job.status = JobDefaults.S_IN_PROGRESS
            result = job.results.select(lambda result: result.hostname == target.id).first()
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

    def get_unpicked(self, target: PDataContainer = None) -> list:
        """
        Get unpicked jobs.

        :param target: client
        :return: list of unpicked jobs or an empty list
        """
        jobs = []
        with orm.db_session(optimistic=False):
            if target is None or not target.id:
                job_selector = orm.select(job for job in Job
                                          for result in job.results
                                          if result.started is None)
            else:
                job_selector = orm.select(job for job in Job
                                          for result in job.results
                                          if result.started is None and result.hostname == target.id)
            for job in job_selector:
                jobs.append(job.clone())

        return jobs

    def get_scheduled(self, target: PDataContainer) -> list:
        """
        Get scheduled jobs for the hostname.

        :param target: target client
        :raises SugarJobStoreException: if no hostname has been specified.
        :return: list of jobs
        """
        if target is None or not target.id:
            raise sugar.lib.exceptions.SugarJobStoreException("No hostname specified")

        jobs = []
        with orm.db_session(optimistic=False):
            for job in orm.select(job for job in Job
                                  for result in job.results if result.fired is None and result.hostname == target.id):
                jobs.append(job.clone())

        return jobs

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
        with orm.db_session(optimistic=False):
            finished = orm.select(job for job in Job if job.jid == jid
                                  for result in job.results
                                  for task in result.tasks
                                  for call in task.calls if call.finished is not None)
            stats.finished = len(finished)
        return stats

    def get_by_jid(self, jid: str, noid: bool = True) -> Job:
        """
        Get a job by jid.

        :param jid: job id.
        :param noid: remove database record ID
        :return: Job object.
        """
        with orm.db_session(optimistic=False):
            job = Job.get(jid=jid)
            if job is not None:
                job = job.clone()
                for result in job.results:
                    host = self.get_host(osid=result.hostname)
                    if host is not None:
                        result.host = host
                    del result.hostname  # TODO: this should be renamed machine_id
                    if noid:
                        del result.id
                    for task in result.tasks:
                        if task.answer:
                            task.answer = json.loads(task.answer)  # Convert string-stored in db JSON into data struct
                return job

    def get_later_then(self, dtm: datetime) -> list:
        """
        Get a jobs that are later than specified datetime.

        :param dtm: datetime threshold.
        :return: list of Job objects
        """
        with orm.db_session(optimistic=False):
            return [job.clone() for job in orm.select(job for job in Job if job.created > dtm)]

    def get_not_finished(self) -> list:
        """
        Get unfinished jobs.

        :return: list of unfinished jobs, where calls are not yet reported
        """
        jobs = []
        with orm.db_session(optimistic=False):
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
        with orm.db_session(optimistic=False):
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
        with orm.db_session(optimistic=False):
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
        with orm.db_session(optimistic=False):
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
        with orm.db_session(optimistic=False):
            return [job.clone() for job in orm.select(job for job in Job if job.tag == tag)]

    def get_all(self, limit=25, offset=0) -> list:
        """
        Get all existing jobs.
        WARNING: This dumps literally everything!!

        :param limit: limit of amount of the returned objects.
        :param offset: offset in the database.

        :return: List of job objects.
        """
        if limit is None:
            limit = 0
        if offset is None:
            offset = 0
        with orm.db_session(optimistic=False):
            if limit + offset:
                result = [job.clone() for job in orm.select(
                    job for job in Job).limit(limit, offset=offset)]
            else:
                result = [job.clone() for job in orm.select(job for job in Job)]
        return result

    def get_all_overview(self, limit=25, offset=0) -> list:
        """
        Get all existing jobs, without an actual results (count only).

        :param limit: limit of amount of the returned objects.
        :param offset: offset in the database.

        :return:
        """
        if limit is None:
            limit = 0
        if offset is None:
            offset = 0
        with orm.db_session(optimistic=False):
            query = orm.select(job for job in Job)
            if limit + offset:
                query = query.limit(limit, offset=offset)
            result = []
            for job in query:
                job = job.clone()
                job.results = len(job.results)
                result.append(job)
        return result

    def expire(self, dtm=None) -> None:
        """
        Swipe over jobs and remove those that already outdated.

        :param dtm: date/time threshold (default last five days)
        :return: None
        """
        if dtm is not None:
            with orm.db_session(optimistic=False):
                orm.delete(job for job in Job if job.created < dtm)
        else:
            raise sugar.lib.exceptions.SugarJobStoreException("Date/time should not be None")

    def expire_to_count(self, cnt=30):
        """
        Remove jobs that are older than specific amount of jobs.

        :param cnt:
        :return:
        """
        alive = 0
        with orm.db_session(optimistic=False):
            for job in orm.select(job for job in Job).order_by(orm.desc(Job.created)):
                if alive < cnt:
                    alive += 1
                else:
                    job.delete()

    def delete_by_jid(self, jid: str) -> None:
        """
        Delete a particular job by JID.

        :param jid: string job id
        :return: None
        """
        if jid is not None:
            with orm.db_session(optimistic=False):
                orm.delete(job for job in Job if job.jid == jid)

    def delete_by_tag(self, tag: str) -> None:
        """
        Delete a particular job by tag

        :param tag: string tag
        :return: None
        """
        if tag is not None:
            with orm.db_session(optimistic=False):
                orm.delete(job for job in Job if job.tag == tag)

    def export(self, jid, path) -> None:
        """
        Export job to some tar archive.

        :param jid: job id
        :param path: path on the server to dump all the job data into an archive.
        :raises SugarJobStoreException: if an archive file already exists
        :return: None
        """
        # TODO: currently result.hostname is actually a machine ID.
        #       It thus exports per machine IDs and this is unreadale.
        #       There should be a generally better conversion from ID to hostname in the DB.

        # pylint: disable=R0914
        os.makedirs(path, exist_ok=True)
        path = "{}/sugar-job-{}.tar.gz".format(path, jid)

        # This should not happen, but still.
        if os.path.exists(path):
            raise sugar.lib.exceptions.SugarJobStoreException("File '{}' already exists".format(path))

        archive = tarfile.open(path, mode="w:gz")
        data = []
        with orm.db_session(optimistic=False):
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
                            data.append(("{}/src-{}.{}.yaml".format(result.hostname, task.idn, call.uri),
                                         call.src, True))
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
        if database.provider is None:
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
