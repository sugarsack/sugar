# coding: utf-8
"""
Job store tests.
"""
import os
import shutil
import json
import datetime
import time
import pytest
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
        self.store = JobStorage(get_config())

    def teardown_method(self):
        """
        Perform teardown after every test method.
        :return:
        """
        self.store.close()
        del self.store
        if os.path.exists(get_config().cache.path):
            shutil.rmtree(get_config().cache.path)

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
        self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())

        job = self.store.get_by_jid(jid)
        assert len(job.tasks) == 2
        assert state.tasklist[0].idn == "install_packages"
        assert state.to_yaml() == job.src

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
        self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())

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
        self.store.report_call(jid=jid, idn=task.idn, uri=call.uri,
                               errcode=127, output=output, finished=datetime.datetime.now())

        job = self.store.get_by_jid(jid)
        for task in job.tasks:
            if task.idn == idn:
                for call in task.calls:
                    if call.uri == uri:
                        assert call.errcode == 127
                        output = json.loads(call.output)
                        assert "error" in output
                        assert "Tupperware" in output["error"]

        stats = self.store.get_done_stats(jid=jid)
        assert stats.percent == 50
        assert stats.tasks == 2
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
            self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())
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
            self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())
            if idx in [4, 7]:
                finished.append(jid)

        # Report two jobs (4th and 7th) as done
        output = json.dumps({"error": "Sysadmin accidentally destroyed pager with a large hammer."})
        for jid in finished:
            job = self.store.get_by_jid(jid)
            for task in job.tasks:
                for call in task.calls:
                    self.store.report_call(jid=jid, idn=task.idn, uri=call.uri,
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
            self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())
            if idx in [4, 7]:
                finished.append(jid)
            else:
                unfinished.append(jid)

        # Report two jobs (4th and 7th) as done
        output = json.dumps({"error": "Sysadmin accidentally destroyed pager with a large hammer."})
        for jid in finished:
            job = self.store.get_by_jid(jid)
            for task in job.tasks:
                for call in task.calls:
                    self.store.report_call(jid=jid, idn=task.idn, uri=call.uri,
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
            self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())
            if idx in [4, 7]:
                failed.append(jid)
            else:
                succeed.append(jid)

        output = json.dumps({"message": "Traffic jam on the Information Superhighway."})
        for jid in failed + succeed:
            job = self.store.get_by_jid(jid)
            for task in job.tasks:
                for call in task.calls:
                    errcode = 1 if jid in failed else 0
                    self.store.report_call(jid=jid, idn=task.idn, uri=call.uri,
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
            self.store.add_tasks(jid, *state.tasklist, job_src=state.to_yaml())
            if idx in [4, 7]:
                failed.append(jid)
            else:
                succeed.append(jid)

        output = json.dumps({"message": "Traffic jam on the Information Superhighway."})
        for jid in failed + succeed:
            job = self.store.get_by_jid(jid)
            for task in job.tasks:
                for call in task.calls:
                    errcode = 1 if jid in failed else 0
                    self.store.report_call(jid=jid, idn=task.idn, uri=call.uri,
                                           errcode=errcode, output=output, finished=datetime.datetime.now())
        for job in self.store.get_suceeded():
            assert job.jid in succeed
            assert job.jid not in failed
            succeed.pop(succeed.index(job.jid))
        assert not succeed

