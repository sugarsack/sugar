# coding: utf-8
"""
Job store tests.
"""
import os
import shutil
import json
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

    def test_update_job(self, get_barestates_root):
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
        assert len(job.tasks) == 1
        assert state.tasklist[0].idn == next(iter(job.tasks)).idn
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
        self.store.report(jid=jid, idn=task.idn, uri=call.uri, errcode=127, output=output)

        job = self.store.get_by_jid(jid)
        for task in job.tasks:
            if task.idn == idn:
                for call in task.calls:
                    if call.uri == uri:
                        assert call.errcode == 127
                        output = json.loads(call.output)
                        assert "error" in output
                        assert "Tupperware" in output["error"]
