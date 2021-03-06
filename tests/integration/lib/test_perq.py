# coding: utf-8
"""
Test Persistent Queue object.
"""
import os
import tempfile
import shutil
import pytest
from sugar.lib.perq import FSQueue
from sugar.lib.perq.qexc import QueueEmpty, QueueFull
from mock import MagicMock, patch
import multiprocessing


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

    def test_ordering(self):
        """
        Get objects in the order.

        :return:
        """
        fsq = FSQueue(self._current_tree)

        fsq.put("one")

        assert fsq.get() == "one"

        fsq.put("two")
        fsq.put("three")
        fsq.put("four")

        assert fsq.get() == "two"

        fsq.put("five")

        assert fsq.get() == "three"

        fsq.put("six")
        fsq.put("seven")
        fsq.put("eight")

        assert fsq.get() == "four"
        assert fsq.get() == "five"
        assert fsq.get() == "six"
        assert fsq.get() == "seven"

        fsq.put("nine")

        assert fsq.get() == "eight"

        fsq.put("ten")

        assert fsq.get() == "nine"
        assert fsq.get() == "ten"

        with pytest.raises(QueueEmpty) as exc:
            fsq.get_nowait()

        assert "Queue is empty" in str(exc)

    @patch("time.sleep", MagicMock(side_effect=Exception("Polling")))
    def test_qsize(self):
        """
        Test qsize method.

        :return:
        """
        fsq = FSQueue(self._current_tree)
        assert fsq.qsize() == 0

        fsq.put("one")
        assert fsq.qsize() == 1

        fsq.put("one")
        assert fsq.qsize() == 2

        fsq.put("one")
        assert fsq.qsize() == 3

        fsq.put("one")
        assert fsq.qsize() == 4

        fsq.get()
        assert fsq.qsize() == 3

        fsq.get()
        assert fsq.qsize() == 2

        fsq.get()
        assert fsq.qsize() == 1

        fsq.get()
        assert fsq.qsize() == 0

        with pytest.raises(Exception) as exc:
            fsq.get()
        assert "Polling" in str(exc)

    def test_notify(self):
        """
        Test notification.

        :return:
        """
        fsq = FSQueue(self._current_tree).use_notify(multiprocessing.Queue())
        assert fsq._mp_notify is not None
        fsq._mp_notify.get = MagicMock(side_effect=Exception("Notified"))
        with pytest.raises(Exception) as exc:
            fsq.get()

        assert "Notified" in str(exc)

    def test_full_empty(self):
        """
        Test queue is full or empty.

        :return:
        """
        fsq = FSQueue(self._current_tree, maxsize=3)
        fsq.put("one")
        fsq.put("two")
        fsq.put("three")

        with pytest.raises(QueueFull) as exc:
            fsq.put("one")
        assert "Queue is full" in str(exc)

        fsq.get_nowait()
        fsq.put("four")
        fsq.get_nowait()
        fsq.get_nowait()
        assert fsq.get_nowait() == "four"
        assert fsq.qsize() == 0
        assert fsq.empty()

    def test_falloc(self):
        """
        Test xlog frame allocation.

        :return:
        """
        fsq = FSQueue(self._current_tree, maxsize=10)

        assert fsq._f_alloc() == "01"
        fsq.put(1)
        assert fsq._f_alloc() == "02"
        fsq.put(2)
        assert fsq._f_alloc() == "03"
        fsq.put(3)

    def test_fdealloc(self):
        """
        Test xlog fram de-allocation.

        :return:
        """
        fsq = FSQueue(self._current_tree, maxsize=10)

        fsq.put(1)
        fsq.put(2)
        fsq.put(3)

        assert fsq._f_dealloc() == "01"
        fsq.get_nowait()
        assert fsq._f_dealloc() == "02"
        fsq.get_nowait()
        assert fsq._f_dealloc() == "03"
        fsq.get_nowait()
        assert fsq._f_dealloc() is None
