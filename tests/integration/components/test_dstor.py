# coding: utf-8
"""
Test data store runtime.
"""
import os
import errno
import shutil
import tempfile
import pickle
from sugar.components.server.cdatastore import CDataStore, CDataContainer


class TestDataStore:
    """
    Test suite for the datastore.
    """
    store_path = None
    store_ref = None

    @classmethod
    def setup_class(cls):
        """
        Setup test suite.

        :return:
        """
        cls.store_path = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        """
        Teardown test suite.

        :return:
        """
        shutil.rmtree(cls.store_path)

    def _remove_inner_tree(self):
        """
        Remove inner tree.
        :return:
        """
        try:
            shutil.rmtree(os.path.join(self.store_path, "sugar"))
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise exc

    def setup_method(self, method):
        """
        Setup method
        :return:
        """
        assert not os.path.exists(os.path.join(self.store_path, "sugar")), "Unclean setup"
        self.store_ref = CDataStore(self.store_path)

    def teardown_method(self, method):
        """
        Teardown method.

        :param method:
        :return:
        """
        self.store_ref = None
        self._remove_inner_tree()

    def test_add_system(self):
        """
        Test add system to the data store.

        :return:
        """
        systems = [
            ("807b8c1a8505c90781f6b4cc37e6cceb", "sugar.domain.org"),
            ("ccd95d7d9247f00ded425c163f43d19a", "candy.domain.org"),
            ("4008ebadf8fd65b33e775e3e98bfb9d7", "latte.domain.org"),
        ]
        for machine_id, hostname in systems:
            container = CDataContainer(id=machine_id, host=hostname)
            container.traits = {"os-family": "Linux", "machine-id": machine_id}
            container.inherencies = {"hostname": hostname}
            self.store_ref.add(container)

        data_path = os.path.join(self.store_path, "sugar", "cdata")
        for filename in os.listdir(data_path):
            assert "." in filename
            fname, ext = filename.split(".")
            assert ext == "data"
            assert fname in [mid[0] for mid in systems]

            with open(os.path.join(data_path, filename), "rb") as dfh:
                obj = pickle.load(dfh)
                assert obj.id == fname
                assert obj.traits["machine-id"] == obj.id == fname

    def test_delete_system(self):
        """
        Test delete system from the data store.

        :return:
        """

    def test_flush_all(self):
        """
        Test flush the data store.

        :return:
        """

    def test_basic_search(self):
        """
        Test basic search over the data store.
        NOTE: this search won't go over the details
        of the particular search corner-cases
        as there are other tests for this matter.

        :return:
        """
