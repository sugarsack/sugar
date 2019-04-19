# coding: utf-8
"""
State collector integration test.
"""
import os
import tempfile
import pytest
import shutil
from sugar.components.client.statecollector import StateCollector
from sugar.utils.jid import jidstore


class TestStateCollector:
    """
    Test suite for the state collector.
    """
    jid = root = None
    prefdir = "/tmp/sugar-statecollector"

    def setup_class(self):
        """
        Setup test class.

        :return: None
        """
        os.makedirs(self.prefdir, exist_ok=True)

    def teardown_class(self):
        """
        Remove test data after finish.

        :return: None
        """
        shutil.rmtree(self.prefdir)

    def setup_method(self, method) -> None:
        """
        Setup each method call.

        :param method: test method
        :return: None
        """
        self.jid = jidstore.create()
        self.root = tempfile.mkdtemp(dir=self.prefdir)
        if os.path.exists(self.root):
            shutil.rmtree(self.root)
        os.makedirs(self.root)

    def teardown_method(self, method):
        """
        Teardown each method call.

        :param method: test method
        :return: None
        """
        shutil.rmtree(self.root)
        self.jid = self.root = None

    def test_next_uri_requested(self):
        """
        Test next URI requested. No source added at all,
        therefore next hop will request the original URI
        :return:
        """
        assert StateCollector(jid=self.jid, uri="test.state").next_hop() == "test.state"

