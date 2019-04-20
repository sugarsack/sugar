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
from sugar.lib.compiler.objtask import FunctionObject


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
        assert StateCollector(jid=self.jid, uri="test.state", root=self.root).next_hop() == "test.state"

    def test_single_resource_added(self):
        """
        Test next URI is not requested on single source add.
        The resource is added with the newline.

        :return:
        """
        src = """
httpd_installed:
  pkg.installed:
    name: nginx
        """
        collector = StateCollector(jid=self.jid, uri="test.state", root=self.root)
        collector.add_resource("test/state.st", source=src)
        target_file = os.path.join(self.root, self.jid, "main/test/state.st")
        assert collector.next_hop() is None
        assert os.path.exists(target_file)
        with open(target_file, "r") as target_fh:
            assert (src.strip() + os.linesep) == target_fh.read()

    def test_multiple_resources_added(self):
        """
        Test next URIs are requested on multi-source add.

        :return:
        """
        resources = (
            ("test/state.st", "test.ssh", """
import:
  - test.ssh
  - test.ssl

httpd_installed:
  pkg.installed:
    name: nginx
"""),
            ("test/ssh.st", "test.ssl", """
ssh_server:
  pkg.installed:
    name: openssh-server
"""),
            ("test/ssl.st", None, """
ssl_keys:
  ssl.create_certificates:
    path: /etc/sugar/pki
""")
        )

        collector = StateCollector(jid=self.jid, uri="test.state", root=self.root)
        for res_path, res_next_hop, res_src in resources:
            collector.add_resource(res_path, source=res_src)
            assert collector.next_hop() == res_next_hop
            target_file = os.path.join(self.root, self.jid, "main", res_path)
            assert os.path.exists(target_file)
            with open(target_file, "r") as target_fh:
                assert (res_src.strip() + os.linesep) == target_fh.read()

        assert collector.tasks is not None
        assert len(collector.tasks) == 3
        expectations = ["ssh_server", "ssl_keys", "httpd_installed"]
        for idx, task in enumerate(collector.tasks):
            assert task.idn == expectations[idx]
            for call in task.calls:
                assert call.type == FunctionObject.TYPE_STATE

    def test_repeatable_reinit_by_jid(self):
        """
        State collector should pick up existing meta/uri by JID instead of making new one.

        :return:
        """
        uri = "test.state"

        # First iteration
        src = """
import:
  - best_editor

add_httpd:
  pkg.installed:
    name: nginx
"""
        collector = StateCollector(jid=self.jid, uri=uri, root=self.root)
        collector.add_resource("test/state.st", source=src)
        assert collector.next_hop() == "best_editor"
        assert "uri" in collector.meta
        assert collector.meta["uri"] == uri

        # Second iteration
        assert StateCollector(jid=self.jid, root=self.root).next_hop() == "best_editor"
        assert "uri" in collector.meta
        assert collector.meta["uri"] == uri

        # Third iteration
        src = """
import:
  - resources.ssl

add_best_editor:
  pkg.installed:
    name: emacs
"""
        collector = StateCollector(jid=self.jid, root=self.root)
        collector.add_resource("best_editor.st", source=src)
        assert collector.next_hop() == "resources.ssl"
        assert "uri" in collector.meta
        assert collector.meta["uri"] == uri

        # Fourth iteration
        assert StateCollector(jid=self.jid, root=self.root).next_hop() == "resources.ssl"
        assert "uri" in collector.meta
        assert collector.meta["uri"] == uri

        # Fifth iteration
        src = """
setup_ssl:
  ssl.certificates.generate:
    scope: all

setup_httpd_configs:
  file.configuration:
    src: sugar://someconfig.cfg
    dest: /etc/nginx/someconfig.cfg
"""
        collector = StateCollector(jid=self.jid, root=self.root)
        collector.add_resource("resources/ssl.st", source=src)
        assert collector.next_hop() is None
        assert "uri" in collector.meta
        assert collector.meta["uri"] == uri
