# coding: utf-8
"""
File-system queue.

This queue implementation should not have any extra-delay
when getting an item.
"""
import os
import time
import errno
import pickle
import multiprocessing

from sugar.lib.perq.queue import Queue
from sugar.lib.perq.qexc import QueueEmpty
from collections import OrderedDict
import sugar.utils.files

try:
    import msgpack
except ImportError:
    msgpack = None


class FSQueue(Queue):
    """
    File-system queue
    """
    MAX_SIZE = 0xfff  # Default max size of the queue
    BUFF = 0xa        # Default buffer
    POLL = 5          # Poll seconds

    def __init__(self, path, maxsize: int = MAX_SIZE, buff: int = BUFF, poll: int = POLL):
        self._queue_path = path
        self._max_size = maxsize
        self._buff_size = buff
        self._buff = OrderedDict()
        self._mutex = False
        self._msgpack = False
        self._mp_notify = None
        self._poll = poll

        try:
            os.makedirs(self._queue_path)
        except (OSError, IOError) as exc:
            if exc.errno != errno.EEXIST:
                raise

    def use_msgpack(self, use=False):
        """
        Set use msgpack instead of pickle.

        This allows much faster serialisation
        and sometimes a bit faster loading.
        However, pickle is used by default to
        deal with the native Python objects.

        :return:
        """
        self._msgpack = use if msgpack is not None else False
        return self

    def use_notify(self):
        """
        Use queue notification between multi processes.

        Every time when put() is called, internal queue also
        accepts an object, which indicates that disk has been changed.
        At that moment get() will re-read the disc store.

        If notify is not used, then disk should be re-read
        in polling fashion, that might be not always suitable.

        This configuration option also assumes that there is
        shared queue and it is transferring messages to an end-point.

        :return:
        """
        self._mp_notify = multiprocessing.Queue()
        return self

    def _lock(self):
        while self._mutex:
            time.sleep(0.01)
        self._mutex = True

    def _unlock(self):
        self._mutex = False

    def empty(self) -> bool:
        """
        Returns True if queue is empty.
        """
        return True

    def full(self) -> bool:
        """
        Returns True if queue is full.
        """
        return False

    def get(self):
        """
        Blocking get.
        """
        return self.__get(wait=True)

    def get_nowait(self):
        """
        Non-blocking get.
        """
        return self.__get()

    def __get(self, wait=False):
        self._lock()
        if wait:
            if self._mp_notify is not None:
                # Use notification protocol
                self._mp_notify.get()
            else:
                # Poll the disk
                while True:
                    if all([True for fname in os.listdir(self._queue_path) if fname.endswith(".xlog")]):
                        break
                    time.sleep(self._poll)

        xlog = self._f_dealloc()
        if xlog is None:
            raise QueueEmpty("Queue is empty")

        frame_log = os.path.join(self._queue_path, "{}.xlog".format(xlog))
        with sugar.utils.files.fopen(frame_log, "rb") as h_frm:
            obj = pickle.load(h_frm)
            os.unlink(frame_log)
        self._unlock()

        return obj

    def _f_dealloc(self):
        """
        Deallocate frame
        """
        try:
            fn = str(list(sorted([int(fname.split(".")[0]) for fname in os.listdir(self._queue_path)]))[0]).zfill(5)
        except IndexError:
            fn = None

        return fn

    def _f_alloc(self):
        """
        Allocate next frame.
        """
        objects = [int(fname.split(".")[0]) for fname in os.listdir(self._queue_path)]
        return str((list(reversed(objects))[0] if objects else 0) + 1).zfill(5)

    def put(self, obj):
        """
        Blocking put.
        """
        self.__put(obj, wait=True)

    def put_nowait(self, obj):
        """
        Non-blocking put.
        """
        self.__put(obj)

    def __put(self, obj, wait: bool = False) -> None:
        """
        Put an object to the FS.

        :param obj: Object to put.
        :param wait: Wait if queue is full.
        :return: None
        """
        self._lock()

        if wait:
            while self.full():
                time.sleep(0.01)

        frame = self._f_alloc()
        with sugar.utils.files.fopen(os.path.join(self._queue_path, "{}.xlog".format(frame)), "wb") as h_frm:
            pickle.dump(obj, h_frm)

        if self._mp_notify is not None:
            self._mp_notify.put_nowait(True)

        self._unlock()

    def qsize(self):
        """
        Return queue size.
        """
        return len(list(os.listdir(self._queue_path)))
