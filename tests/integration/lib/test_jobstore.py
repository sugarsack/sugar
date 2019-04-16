# coding: utf-8
"""
Job store tests.
"""
import os
import shutil
import json
import pytz
import datetime
import time
import tarfile
import hashlib

import pytest

import sugar.lib.exceptions
import sugar.utils.timeutils
from sugar.lib.compiler import StateCompiler
from sugar.config import get_config
from tests.integration.fixtures import get_barestates_root
from sugar.components.server.pdatastore import PDataContainer
from sugar.lib.jobstore.const import JobTypes


@pytest.fixture
def targets_list():
    """
    Targets list.

    :return:
    """
    out = []
    targets = ["web.sugarsack.org", "docs.sugarsack.org"]
    for hostname in targets:
        out.append(PDataContainer(id=hashlib.md5(hostname.encode("utf-8")).hexdigest(), host=hostname))

    return out


class TestBasicJobStore:
    """
    Basic Job Store test suite (e.g. db works at all).
    """
    def setup_method(self):
        """
        Perform setup before every test method.
        :return:
        """
        from sugar.lib.jobstore import JobStorage

        self._path = "/tmp/jobstore"
        self.store = JobStorage(get_config(), path=self._path)

    def teardown_method(self):
        """
        Perform teardown after every test method.
        :return:
        """
        self.store.close()
        if os.path.exists(self._path):
            shutil.rmtree(self._path)
        del self.store
        del self._path

    def test_register_job(self, targets_list):
        """
        Register a job into a job cache. This is happening when either
        state or a command is issued. Here no job yet is even compiled.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"

        jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
        obj = self.store.get_by_jid(jid)
        assert obj.jid == jid
        for result in obj.results:
            for task in result.tasks:
                assert task.machineid in [target.id for target in targets_list]

    def test_add_tasks(self, get_barestates_root, targets_list):
        """
        Update job.

        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        # Create task
        jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
        # Client compiles it
        state = StateCompiler(get_barestates_root).compile(uri)

        # Client updates the server
        for target in targets_list:
            self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())

        job = self.store.get_by_jid(jid)
        for result in job.results:
            assert len(result.tasks) == 2
            assert result.src == state.to_yaml()

    def test_report_task(self, get_barestates_root, targets_list):
        """
        Report task done.

        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"

        # Create task
        jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
        # Client compiles it
        state = StateCompiler(get_barestates_root).compile(uri)

        # Client updates the server
        for target in targets_list:
            self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())

        assert len(state.tasklist) == 2
        task = next(iter(state.tasklist))
        assert task is not None

        assert bool(len(task.calls))
        call = next(iter(task.calls))
        assert call is not None

        # Function finishes, the output is reported
        output = json.dumps({"error": "Stale file handle (next time use Tupperware(tm)!)"})
        idn = task.idn
        uri = call.uri
        self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, target=targets_list[0],
                               errcode=127, output=output, finished=datetime.datetime.now(tz=pytz.UTC))

        job = self.store.get_by_jid(jid)
        for result in job.results:
            if result.hostname != targets_list[0]:
                continue
            for task in result.tasks:
                if task.idn == idn:
                    for call in task.calls:
                        if call.uri == uri:
                            assert call.errcode == 127
                            output = json.loads(call.output)
                            assert "error" in output
                            assert "Tupperware" in output["error"]

        stats = self.store.get_done_stats(jid=jid)
        assert stats.percent == 25
        assert stats.tasks == 4
        assert stats.finished == 1

    def test_get_later_than(self, get_barestates_root, targets_list):
        """
        Test get later than particular date/time.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"

        print()
        begin = datetime.datetime.now(tz=pytz.UTC)
        middle = None
        for idx in range(10):
            if idx == 4:
                middle = datetime.datetime.now(tz=pytz.UTC)
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            print("Adding job", idx + 1, "of 10, JID:", jid)
            time.sleep(1)
        end = datetime.datetime.now(tz=pytz.UTC)

        assert len(self.store.get_later_then(begin)) == 10
        middle = len(self.store.get_later_then(middle))
        assert 7 > middle > 4
        assert len(self.store.get_later_then(end)) == 0

    def test_get_finished(self, get_barestates_root, targets_list):
        """
        Test get all tasks that are finished.

        :param get_barestates_root:
        :param targets_list:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        finished = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            if idx in [4, 7]:
                finished.append(jid)

        # Report two jobs (4th and 7th) as done
        output = json.dumps({"error": "Sysadmin accidentally destroyed pager with a large hammer."})
        for jid in finished:
            job = self.store.get_by_jid(jid)
            for result in job.results:
                for task in result.tasks:
                    for call in task.calls:
                        for target in targets_list:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, target=target,
                                                   errcode=127, output=output,
                                                   finished=datetime.datetime.now(tz=pytz.UTC))
        for job in self.store.get_finished():
            assert job.jid in finished
            finished.pop(finished.index(job.jid))
        assert not finished

    def test_get_unfinished(self, get_barestates_root, targets_list):
        """
        Test get all tasks that are not finished.

        :param get_barestates_root:
        :param targets_list:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        finished = []
        unfinished = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            if idx in [4, 7]:
                finished.append(jid)
            else:
                unfinished.append(jid)

        # Report two jobs (4th and 7th) as done
        output = json.dumps({"error": "Sysadmin accidentally destroyed pager with a large hammer."})
        for jid in finished:
            job = self.store.get_by_jid(jid)
            for result in job.results:
                for task in result.tasks:
                    for call in task.calls:
                        for target in targets_list:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, target=target,
                                                   errcode=127, output=output,
                                                   finished=datetime.datetime.now(tz=pytz.UTC))
        for job in self.store.get_not_finished():
            assert job.jid in unfinished
            assert job.jid not in finished
            unfinished.pop(unfinished.index(job.jid))
        assert not unfinished

    def test_get_failed_jobs(self, get_barestates_root, targets_list):
        """
        Test get all tasks that are failed (error code is not EX_OK).

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        failed = []
        succeed = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            if idx in [4, 7]:
                failed.append(jid)
            else:
                succeed.append(jid)

        output = json.dumps({"message": "Traffic jam on the Information Superhighway."})
        for jid in failed + succeed:
            job = self.store.get_by_jid(jid)
            for result in job.results:
                for task in result.tasks:
                    for call in task.calls:
                        errcode = 1 if jid in failed else 0
                        for target in targets_list:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, target=target,
                                                   errcode=errcode, output=output,
                                                   finished=datetime.datetime.now(tz=pytz.UTC))
        for job in self.store.get_failed():
            assert job.jid in failed
            assert job.jid not in succeed
            failed.pop(failed.index(job.jid))
        assert not failed

    def test_get_succeeded_jobs(self, get_barestates_root, targets_list):
        """
        Test get all tasks that are failed (error code is not EX_OK).

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        failed = []
        succeed = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            if idx in [4, 7]:
                failed.append(jid)
            else:
                succeed.append(jid)

        output = json.dumps({"message": "Traffic jam on the Information Superhighway."})
        for jid in failed + succeed:
            job = self.store.get_by_jid(jid)
            for result in job.results:
                for task in result.tasks:
                    for call in task.calls:
                        errcode = 1 if jid in failed else 0
                        for target in targets_list:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, target=target,
                                                   errcode=errcode, output=output,
                                                   finished=datetime.datetime.now(tz=pytz.UTC))
        for job in self.store.get_suceeded():
            assert job.jid in succeed
            assert job.jid not in failed
            succeed.pop(succeed.index(job.jid))
        assert not succeed

    def test_get_tagged_jobs(self, get_barestates_root, targets_list):
        """
        Test get all tagged jobs

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        _tag = "#everything_on_fire"
        tagged = []
        for idx in range(10):
            tag = _tag if idx in [4, 7] else None
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="",
                                 job_type=JobTypes.RUNNER, tag=tag)
            if tag is not None:
                tagged.append(jid)
            state = StateCompiler(get_barestates_root).compile(uri)
            for target in targets_list:
                self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
        for job in self.store.get_by_tag(tag=_tag):
            assert job.jid in tagged
            tagged.pop(tagged.index(job.jid))
        assert not tagged

    def test_get_all_jobs(self, targets_list):
        """
        Test get all jobs with pagination and offset.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        for idx in range(100):
            self.store.new(query=query, clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)

        assert len(self.store.get_all(limit=None, offset=0)) == 100
        assert len(self.store.get_all(limit=25, offset=0)) == 25

    def test_expire_jobs(self, targets_list):
        """
        Test expire jobs.

        :return:
        """
        query = ":a"
        uri = "job_store.test_jobstore_register_job"
        print()
        middle = None
        tag = "#outdated"
        for idx in range(10):
            if idx == 8:
                middle = datetime.datetime.now(tz=pytz.UTC)
                tag = None
            jid = self.store.new(query=query, clientslist=targets_list, uri=uri, args="",
                                 job_type=JobTypes.RUNNER, tag=tag)
            print("Adding job", idx + 1, "of 10, JID:", jid)
            time.sleep(1.5)
        self.store.expire(middle)
        assert len(self.store.get_all()) == 2
        assert not bool(self.store.get_by_tag(tag="#outdated"))

    def test_export_to_archive_jobs(self, get_barestates_root, targets_list):
        """
        Test export to an archive jobs.

        :param targets_list
        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        for target in targets_list:
            self.store.add_host(fqdn=target.host, osid=target.id, ipv4="127.0.0.1", ipv6="::1")

        jid = self.store.new(query="*", clientslist=targets_list, uri=uri, args="",
                             job_type=JobTypes.RUNNER, tag="for exporting")
        state = StateCompiler(get_barestates_root).compile(uri)
        for target in targets_list:
            self.store.add_tasks(jid, *state.tasklist, target=target, src=state.to_yaml())
            self.store.report_job(jid=jid, target=target, src=state.to_yaml(), return_data="{}",
                                  finished=datetime.datetime.now(), uri=uri)

        self.store.export(jid, path=self._path)

        archpath = "{}/sugar-job-{}.tar.gz".format(self._path, jid)
        arch_extracted_path = "{}/archive/".format(self._path)
        tar = tarfile.open(archpath)
        tar.extractall(arch_extracted_path)
        tar.close()

        assert os.path.exists("{}job-info.yaml".format(arch_extracted_path))
        for target in targets_list:
            assert os.path.exists("{}{}".format(arch_extracted_path, target.host))
            for f_gen in ["source", "result"]:
                assert os.path.exists("{}{}/{}.yaml".format(arch_extracted_path, target.host, f_gen))

    def test_report_job_result(self, get_barestates_root, targets_list):
        """
        Test job reporting.

        :param get_barestates_root:
        :param targets_list:
        :return:
        """
        uri = "job_store.test_jobstore_register_job"

        state = StateCompiler(get_barestates_root).compile(uri)

        jid = self.store.new(query="*", clientslist=targets_list, uri=uri, args="",
                             job_type=JobTypes.RUNNER, tag="for exporting")
        target = targets_list[0]
        return_data = {
            "some": "structure",
            "value": 42,
            "messages": ["first line", "second line"]
        }

        log = {
            "info": [
                "Mar 27 18:16:47 zeus AptDaemon: INFO: Quitting due to inactivity",
                "Mar 27 18:16:47 zeus AptDaemon: INFO: Quitting was requested",
                "Mar 27 18:16:47 zeus org.freedesktop.PackageKit[1052]: 18:16:47 AptDaemon [INFO]: "
                "Quitting due to inactivity",
                "Mar 27 18:16:47 zeus org.freedesktop.PackageKit[1052]: 18:16:47 AptDaemon [INFO]: "
                "Quitting was requested",
            ],
            "warn": [
                "Mar 27 18:16:47 zeus org.freedesktop.PackageKit[1052]: 18:16:47 AptDaemon [WARN]: "
                "Quitting probaby did not succeed",
            ],
            "err": [
                "Mar 27 18:17:01 zeus CRON[4890]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)",
            ],
        }

        self.store.report_job(jid=jid, target=target, src=state.to_yaml(),
                              return_data=json.dumps(return_data), finished=datetime.datetime.now(),
                              log_info=json.dumps(log["info"]), log_warn=json.dumps(log["warn"]),
                              log_err=json.dumps(log["err"]))

        job = self.store.get_by_jid(jid)
        for result in job.results:
            if result.hostname == target.id:
                assert result.src == state.to_yaml()
            else:
                for task in result.tasks:
                    assert task.return_data == return_data
                    assert task.log_info == log["info"]
                    assert task.log_warn == log["warn"]
                    assert task.log_err == log["err"]

    def test_delete_job_by_jid(self, targets_list):
        """
        Delete job by jid.

        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        jid = self.store.new(query="*", clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER)
        assert self.store.get_by_jid(jid=jid) is not None
        self.store.delete_by_jid(jid=jid)
        assert self.store.get_by_jid(jid=jid) is None

    def test_delete_job_by_tag(self, targets_list):
        """
        Delete job by tag.

        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        tag = "test"
        for x in range(10):
            self.store.new(query="*", clientslist=targets_list, uri=uri, args="", job_type=JobTypes.RUNNER,
                           tag=None if x in [2, 4, 6] else tag)

        assert len(self.store.get_all()) == 10

        self.store.delete_by_tag(tag)
        jobs = self.store.get_all()

        assert len(jobs) == 3
        for job in jobs:
            assert job.tag is None

    def test_get_scheduled(self, targets_list):
        """
        Get scheduled jobs for the offline client.

        :return:
        """
        self.store.new(query="*", clientslist=[targets_list[0]], uri="some.uri", args="", job_type=JobTypes.RUNNER)
        assert len(self.store.get_all()) == 1
        assert len(self.store.get_scheduled(targets_list[0])) == 1
        assert len(self.store.get_scheduled(targets_list[0], mark=True)) == 1
        assert len(self.store.get_scheduled(targets_list[0])) == 0

    def test_get_scheduled_no_hostname(self, targets_list):
        """
        Raise an exception if hostname is not specified.

        :return:
        """
        self.store.new(query="*", clientslist=[targets_list[0]], uri="some.uri", args="", job_type=JobTypes.RUNNER)
        assert len(self.store.get_all()) == 1
        with pytest.raises(sugar.lib.exceptions.SugarJobStoreException) as exc:
            self.store.get_scheduled(None)
        assert "No hostname specified" in str(exc)

    def test_get_unpicked(self, targets_list):
        """
        Test getting unpicked jobs for one host or many.

        :return:
        """
        hosts = []
        for hostname in ["madcow.domain.foo", "flyingpig.domain.foo"]:
            targets_list.append(PDataContainer(id=hashlib.md5(hostname.encode("utf-8")).hexdigest(), host=hostname))

        for idx in range(2):
            self.store.new(query="*", clientslist=targets_list, uri="some.uri", args="", job_type=JobTypes.RUNNER)
        for idx in range(2):
            self.store.new(query="*", clientslist=targets_list[1:], uri="some.uri", args="", job_type=JobTypes.RUNNER)
        assert len(self.store.get_unpicked()) == 4
        assert len(self.store.get_unpicked(target=targets_list[0])) == 2

    def test_fire_job(self, targets_list):
        """
        Test fire job.
        :return:
        """
        jid = self.store.new(query=":a", clientslist=[targets_list[0]], uri="some.url",
                             args="", job_type=JobTypes.RUNNER)
        for result in self.store.get_by_jid(jid=jid).results:
            if result.hostname in [targets_list[0].id]:
                assert result.fired is None

        for target in targets_list:
            self.store.set_as_fired(jid, target=target)

        for result in self.store.get_by_jid(jid=jid).results:
            if result.hostname in [targets_list[0].id]:
                assert result.fired is not None

    def test_add_host(self):
        """
        Add host several times that expected to be added only once.

        :return:
        """
        for args in [{"fqdn": "gorilla.domain.lan", "osid": hashlib.md5(b"123").hexdigest(),
                      "ipv4": "10.190.1.1", "ipv6": None}]:
            for _ in range(10):
                self.store.add_host(**args)
        host = self.store.get_host(fqdn="gorilla.domain.lan")
        assert host.fqdn == "gorilla.domain.lan"
        assert host.ipv4 == "10.190.1.1"
