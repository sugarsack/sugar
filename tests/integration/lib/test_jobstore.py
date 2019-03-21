# coding: utf-8
"""
Job store tests.
"""
import pytest
from sugar.lib.jobstore import JobStorage
from sugar.config import get_config
from tests.integration.fixtures import get_barestates_root


class TestJobStore:
    """
    Job Store test suite.
    """
    def test_register_job(self, get_barestates_root):
        """
        Register a job into a job cache. This is happening when either
        state or a command is issued. Here no job yet is even compiled.

        :param get_barestates_root:
        :return:
        """
        query = ":a"
        clientslist = ["web.sugarsack.org", "docs.sugarsack.org"]
        expr = "job_store.test_jobstore_register_job"

        store = JobStorage(get_config())
        jid = store.new(query=query, clientslist=clientslist, expr=expr)

    def test_update_job(self):
        """
        Update job.

        :return:
        """
