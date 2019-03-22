# coding: utf-8
"""
Job store tests.
"""
import os
import shutil
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
        assert self.store.get_by_jid(jid).jid == jid

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
        assert self.store.get_by_jid(jid).jid == jid

        # Client compiles it
        state = StateCompiler(get_barestates_root).compile(uri)

        # Client updates the server
        self.store.add_tasks(jid, *state.tasklist)
        job = self.store.get_by_jid(jid)

        assert len(job.tasks) == 1
        assert state.tasklist[0].idn == next(iter(job.tasks)).idn
