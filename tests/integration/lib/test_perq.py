# coding: utf-8
"""
Test Persistent Queue object.
"""
import os
import tempfile
import shutil
import pytest
from sugar.lib.perq import FSQueue
from sugar.lib.perq.qexc import QueueEmpty
from mock import MagicMock, patch


class TestFSQueue:
    """
    Persistent FS Queue test suite class.
    """
    root_path = None
    _current_tree = None

    def setup_class(self):
        """
        Setting up test suite session.
        """
        self.root_path = os.path.join(os.path.dirname(__file__), "perq")
        os.makedirs(self.root_path)

    def teardown_class(self):
        """
        Tearing down test suite session.
        """
        try:
            shutil.rmtree(self.root_path)
        except (IOError, OSError) as err:
            print("Error removing test suite temporary data:", err)

    def setup_method(self):
        """
        Setup method
        """
        self._current_tree = tempfile.mkdtemp(dir=self.root_path)

    def teardown_method(self):
        """
        Teardown method.
        """
        try:
            shutil.rmtree(self._current_tree)
        except (IOError, OSError) as err:
            print("Error removing current method temporary data:", err)

    def test_add(self):
        """
        Add an object to the queue.

        :return:
        """
        fsq = FSQueue(self._current_tree)
        for obj in ["one", "two", "three"]:
            fsq.put(obj)
        assert fsq.qsize() == 3

    def test_get(self):
        """
        Get an object from the queue.

        :return:
        """
        fsq = FSQueue(self._current_tree)
        for obj in ["one", "two", "three"]:
            fsq.put(obj)

        assert fsq.get() == "one"
        assert fsq.get() == "two"
        assert fsq.get() == "three"

    def test_empty_get_nowait(self):
        """
        Get an object from the queue immediately if there is nothing.
        This should just raise an exception QueueEmpty.

        :return:
        """

        fsq = FSQueue(self._current_tree)
        with pytest.raises(QueueEmpty) as exc:
            fsq.get_nowait()

        assert "Queue is empty" in str(exc)

    @patch("time.sleep", MagicMock(side_effect=Exception("Polling")))
    def test_empty_get(self):
        """
        Get an object from the queue if there is nothing.

        :return:
        """
        fsq = FSQueue(self._current_tree)
        with pytest.raises(Exception) as exc:
            fsq.get()
        assert "Polling" in str(exc)

