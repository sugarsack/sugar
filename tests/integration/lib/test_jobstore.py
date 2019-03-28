# coding: utf-8
"""
Job store tests.
"""
import os
import shutil
import json
import datetime
import time
import tarfile

import pytest

import sugar.lib.exceptions
from sugar.lib.compiler import StateCompiler
from sugar.lib.jobstore import JobStorage
from sugar.config import get_config
from tests.integration.fixtures import get_barestates_root


class TestBasicJobStore:
    """
    Basic Job Store test suite (e.g. db works at all).
    """
    def setup_method(self):
        """
        Perform setup before every test method.
        :return:
        """
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

    def test_register_job(self):
        """
        Register a job into a job cache. This is happening when either
        state or a command is issued. Here no job yet is even compiled.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"

        jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
        obj = self.store.get_by_jid(jid)
        assert obj.jid == jid
        for result in obj.results:
            assert result.hostname in clientslist

    def test_add_tasks(self, get_barestates_root):
        """
        Update job.

        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"

        # Create task
        jid = self.store.new(query=query, clientslist=clientslist, expr=uri)

        # Client compiles it
        state = StateCompiler(get_barestates_root).compile(uri)

        # Client updates the server
        for hostname in clientslist:
            self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())

        job = self.store.get_by_jid(jid)
        for result in job.results:
            assert result.src == state.to_yaml()
            assert len(result.tasks) == 2

    def test_report_task(self, get_barestates_root):
        """
        Report task done.

        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"

        # Create task
        jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
        # Client compiles it
        state = StateCompiler(get_barestates_root).compile(uri)

        # Client updates the server
        for hostname in clientslist:
            self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())

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
        self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, hostname=clientslist[0],
                               errcode=127, output=output, finished=datetime.datetime.now())

        job = self.store.get_by_jid(jid)
        for result in job.results:
            if result.hostname != clientslist[0]:
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

    def test_get_later_than(self, get_barestates_root):
        """
        Test get later than particular date/time.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"

        print()
        begin = datetime.datetime.now()
        middle = None
        for idx in range(10):
            if idx == 4:
                middle = datetime.datetime.now()
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
            print("Adding job", idx + 1, "of 10, JID:", jid)
            time.sleep(1)
        end = datetime.datetime.now()

        assert len(self.store.get_later_then(begin)) == 10
        middle = len(self.store.get_later_then(middle))
        assert 7 > middle > 4
        assert len(self.store.get_later_then(end)) == 0

    def test_get_finished(self, get_barestates_root):
        """
        Test get all tasks that are finished.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        finished = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
            if idx in [4, 7]:
                finished.append(jid)

        # Report two jobs (4th and 7th) as done
        output = json.dumps({"error": "Sysadmin accidentally destroyed pager with a large hammer."})
        for jid in finished:
            job = self.store.get_by_jid(jid)
            for result in job.results:
                for task in result.tasks:
                    for call in task.calls:
                        for hostname in clientslist:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, hostname=hostname,
                                                   errcode=127, output=output, finished=datetime.datetime.now())
        for job in self.store.get_finished():
            assert job.jid in finished
            finished.pop(finished.index(job.jid))
        assert not finished

    def test_get_unfinished(self, get_barestates_root):
        """
        Test get all tasks that are not finished.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        finished = []
        unfinished = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
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
                        for hostname in clientslist:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, hostname=hostname,
                                                   errcode=127, output=output, finished=datetime.datetime.now())
        for job in self.store.get_not_finished():
            assert job.jid in unfinished
            assert job.jid not in finished
            unfinished.pop(unfinished.index(job.jid))
        assert not unfinished

    def test_get_failed_jobs(self, get_barestates_root):
        """
        Test get all tasks that are failed (error code is not EX_OK).

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        failed = []
        succeed = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
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
                        for hostname in clientslist:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, hostname=hostname,
                                                   errcode=errcode, output=output, finished=datetime.datetime.now())
        for job in self.store.get_failed():
            assert job.jid in failed
            assert job.jid not in succeed
            failed.pop(failed.index(job.jid))
        assert not failed

    def test_get_succeeded_jobs(self, get_barestates_root):
        """
        Test get all tasks that are failed (error code is not EX_OK).

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        failed = []
        succeed = []
        for idx in range(10):
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
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
                        for hostname in clientslist:
                            self.store.report_call(jid=jid, idn=task.idn, uri=call.uri, hostname=hostname,
                                                   errcode=errcode, output=output, finished=datetime.datetime.now())
        for job in self.store.get_suceeded():
            assert job.jid in succeed
            assert job.jid not in failed
            succeed.pop(succeed.index(job.jid))
        assert not succeed

    def test_get_tagged_jobs(self, get_barestates_root):
        """
        Test get all tagged jobs

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        _tag = "#everything_on_fire"
        tagged = []
        for idx in range(10):
            tag = _tag if idx in [4, 7] else None
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri, tag=tag)
            if tag is not None:
                tagged.append(jid)
            state = StateCompiler(get_barestates_root).compile(uri)
            for hostname in clientslist:
                self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())
        for job in self.store.get_by_tag(tag=_tag):
            assert job.jid in tagged
            tagged.pop(tagged.index(job.jid))
        assert not tagged

    def test_get_all_jobs(self):
        """
        Test get all jobs with pagination and offset.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        for idx in range(100):
            self.store.new(query=query, clientslist=clientslist, expr=uri)

        assert len(self.store.get_all(limit=None, offset=0)) == 100
        assert len(self.store.get_all(limit=25, offset=0)) == 25

    def test_expire_jobs(self):
        """
        Test expire jobs.

        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        uri = "job_store.test_jobstore_register_job"
        print()
        middle = None
        tag = "#outdated"
        for idx in range(10):
            if idx == 8:
                middle = datetime.datetime.now()
                tag = None
            jid = self.store.new(query=query, clientslist=clientslist, expr=uri, tag=tag)
            print("Adding job", idx + 1, "of 10, JID:", jid)
            time.sleep(1.5)
        self.store.expire(middle)
        assert len(self.store.get_all()) == 2
        assert not bool(self.store.get_by_tag(tag="#outdated"))

    def test_export_to_archive_jobs(self, get_barestates_root):
        """
        Test export to an archive jobs.

        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        hostnames = ["foo.example.lan", "bar.example.lan"]

        jid = self.store.new(query="*", clientslist=hostnames, expr=uri, tag="for exporting")
        state = StateCompiler(get_barestates_root).compile(uri)
        for hostname in hostnames:
            self.store.add_tasks(jid, *state.tasklist, hostname=hostname, src=state.to_yaml())

        self.store.export(jid, path=self._path)

        archpath = "{}/sugar-job-{}.tar.gz".format(self._path, jid)
        assert os.path.exists(archpath)

        arch_extracted_path = "{}/arch/".format(self._path)
        tar = tarfile.open(archpath)
        tar.extractall(arch_extracted_path)
        tar.close()

        assert os.path.exists("{}job-info.yaml".format(arch_extracted_path))
        for hostname in hostnames:
            assert os.path.exists("{}{}".format(arch_extracted_path, hostname))
            for f_gen in ["source", "result"]:
                assert os.path.exists("{}{}/{}.yaml".format(arch_extracted_path, hostname, f_gen))

    def test_report_job_result(self, get_barestates_root):
        """
        Test job reporting.

        :param get_barestates_root:
        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        hostnames = ["foo.example.lan", "bar.example.lan"]

        state = StateCompiler(get_barestates_root).compile(uri)

        jid = self.store.new(query="*", clientslist=hostnames, expr=uri, tag="for exporting")
        hostname = hostnames[0]
        answer = {
            "some": "structure",
            "value": 42,
            "messages" : [
                "first line",
                "second line"
            ]
        }
        log = """
Mar 27 18:16:47 zeus AptDaemon: INFO: Quitting due to inactivity
Mar 27 18:16:47 zeus AptDaemon: INFO: Quitting was requested
Mar 27 18:16:47 zeus org.freedesktop.PackageKit[1052]: 18:16:47 AptDaemon [INFO]: Quitting due to inactivity
Mar 27 18:16:47 zeus org.freedesktop.PackageKit[1052]: 18:16:47 AptDaemon [INFO]: Quitting was requested
Mar 27 18:17:01 zeus CRON[4890]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)
"""
        self.store.report_job(jid=jid, hostname=hostname, src=state.to_yaml(),
                              log=log, answer=json.dumps(answer))

        job = self.store.get_by_jid(jid)
        for result in job.results:
            if result.hostname == hostname:
                assert result.log == log.strip()
                assert result.src == state.to_yaml()
            else:
                assert result.log == result.src == ""

    def test_delete_job_by_jid(self):
        """
        Delete job by jid.

        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        hostnames = ["foo.example.lan", "bar.example.lan"]
        jid = self.store.new(query="*", clientslist=hostnames, expr=uri)
        assert self.store.get_by_jid(jid=jid) is not None
        self.store.delete_by_jid(jid=jid)
        assert self.store.get_by_jid(jid=jid) is None

    def test_delete_job_by_tag(self):
        """
        Delete job by tag.

        :return:
        """
        uri = "job_store.test_jobstore_register_job"
        tag = "test"
        hostnames = ["foo.example.lan", "bar.example.lan"]
        for x in range(10):
            self.store.new(query="*", clientslist=hostnames, expr=uri, tag=None if x in [2, 4, 6] else tag)

        assert len(self.store.get_all()) == 10

        self.store.delete_by_tag(tag)
        jobs = self.store.get_all()

        assert len(jobs) == 3
        for job in jobs:
            assert job.tag is None

    def test_get_scheduled(self):
        """
        Get scheduled jobs for the offline client.

        :return:
        """
        hostname = "foo"
        self.store.new(query="*", clientslist=[hostname], expr="some.uri")
        assert len(self.store.get_all()) == 1
        assert len(self.store.get_scheduled(hostname)) == 1
        assert len(self.store.get_scheduled(hostname)) == 0

    def test_get_scheduled_no_hostname(self):
        """
        Raise an exception if hostname is not specified.

        :return:
        """
        hostname = "foo"
        self.store.new(query="*", clientslist=[hostname], expr="some.uri")
        assert len(self.store.get_all()) == 1
        with pytest.raises(sugar.lib.exceptions.SugarJobStoreException) as exc:
            self.store.get_scheduled(None)
        assert "No hostname specified" in str(exc)

    def test_get_unpicked(self):
        """
        Test getting unpicked jobs for one host or many.

        :return:
        """
        hostnames = ["madcow.domain.foo", "flyingpig.domain.foo", "frozenhell.domain.foo"]
        for idx in range(2):
            self.store.new(query="*", clientslist=hostnames, expr="some.uri")
        for idx in range(2):
            self.store.new(query="*", clientslist=hostnames[1:], expr="some.uri")
        assert len(self.store.get_unpicked()) == 4
        assert len(self.store.get_unpicked(hostname=hostnames[0])) == 2

    def test_fire_job(self):
        """
        Test fire job.
        :return:
        """
        hostnames = ["some.hostname"]
        jid = self.store.new(query=":a", clientslist=hostnames, expr="some.url")
        for result in self.store.get_by_jid(jid=jid).results:
            if result.hostname in hostnames:
                assert result.fired is None

        for hostname in hostnames:
            self.store.set_as_fired(jid, hostname=hostname)

        for result in self.store.get_by_jid(jid=jid).results:
            if result.hostname in hostnames:
                assert result.fired is not None
