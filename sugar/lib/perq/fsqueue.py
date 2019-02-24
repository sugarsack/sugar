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
from sugar.lib.perq.qexc import QueueEmpty, QueueFull
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
    POLL = 5          # Poll seconds

    def __init__(self, path, maxsize: int = MAX_SIZE, poll: int = POLL):
        self._queue_path = path
        self._max_size = maxsize
        self._xpad = len(str(self._max_size))
        self._mutex = False
        self._serialiser = pickle
        self._mp_notify = None
        self._poll = poll

        try:
            os.makedirs(self._queue_path)
        except (OSError, IOError) as exc:
            if exc.errno != errno.EEXIST:
                raise

    def use_msgpack(self, use=False) -> Queue:
        """
        Set use msgpack instead of pickle.

        This allows much faster serialisation
        and sometimes a bit faster loading.
        However, pickle is used by default to
        deal with the native Python objects.

        :param use: boolean, used to turn on/off msgpack usage. Default is pickle.
        :return: Queue
        """
        self._serialiser = msgpack if msgpack is not None and use else pickle
        return self

    def use_notify(self, queue=None) -> Queue:
        """
        Use queue notification between multi processes via "multiprocessing.Queue".

        Every time when put() is called, internal queue also
        accepts an object, which indicates that disk has been changed.
        At that moment get() will re-read the disc store.

        If notify is not used, then disk should be re-read
        in polling fashion, that might be not always suitable.

        This configuration option also assumes that there is
        shared queue and it is transferring messages to an end-point.

        :param queue: commonly shared queue object. Usually multiprocessing.Queue (default)
        :return: Queue
        """
        self._mp_notify = queue or multiprocessing.Queue()
        return self

    def _lock(self) -> None:
        """
        Lock mutex of the FS

        :return: None
        """
        while self._mutex:
            time.sleep(0.01)
        self._mutex = True

    def _unlock(self) -> None:
        """
        Unlock mutex of the FS.

        :return: None
        """
        self._mutex = False

    def empty(self) -> bool:
        """
        Returns True if queue is empty.

        :return: True if Queue is empty
        """
        return bool(not self.qsize())

    def full(self) -> bool:
        """
        Returns True if queue is full.

        :return: True if queue is full.
        """
        return bool(self.qsize() >= self._max_size)

    def get(self):
        """
        Get an object in blocking mode.

        :return: object
        """
        return self.__get(wait=True)

    def get_nowait(self):
        """
        Get an object in non-blocking mode.

        :return: object
        """
        return self.__get()

    def __get(self, wait: bool = False):
        self._lock()
        if wait:
            if self._mp_notify is not None:
                # Use notification protocol
                self._mp_notify.get()
            else:
                # Poll the disk
                while True:
                    if bool([True for fname in os.listdir(self._queue_path) if fname.endswith(".xlog")]):
                        break
                    time.sleep(self._poll)

        xlog = self._f_dealloc()
        if xlog is None:
            raise QueueEmpty("Queue is empty")

        frame_log = os.path.join(self._queue_path, "{}.xlog".format(xlog))
        h_frm = sugar.utils.files.fopen(frame_log, "rb")
        obj = self._serialiser.load(h_frm)
        h_frm.flush()
        h_frm.close()
        os.unlink(frame_log)
        self._unlock()

        return obj

    def _f_dealloc(self) -> str:
        """
        Deallocate xlog frame.

        :return: name of the previous xlog frame
        """
        frn = [int(fname.split(".")[0]) for fname in os.listdir(self._queue_path)]
        return str(min(frn)).zfill(self._xpad) if frn else None

    def _f_alloc(self) -> str:
        """
        Allocate next xlog frame.

        :return: name of the next xlog frame
        """
        return str(max([int(fnm.split(".")[0]) for fnm in os.listdir(self._queue_path)] + [0]) + 1).zfill(self._xpad)

    def put(self, obj) -> None:
        """
        Blocking put.

        :param obj: object to put
        :return: None
        """
        self.__put(obj, wait=True)

    def put_nowait(self, obj) -> None:
        """
        Non-blocking put.

        :param obj: object to put
        :return: None
        """
        self.__put(obj)

    def __put(self, obj, wait: bool = False) -> None:
        """
        Put an object to the FS.

        :param obj: Object to put.
        :param wait: Wait if queue is full.
        :return: None
        """
        if self.full():
            raise QueueFull("Queue is full")

        self._lock()

        if wait:
            while self.full():
                time.sleep(0.01)

        frame = self._f_alloc()
        xlog_path = os.path.join(self._queue_path, "{}.xlog".format(frame))
        xlog_path_tmp = "{}.temp".format(xlog_path)
        h_frm = sugar.utils.files.fopen(xlog_path_tmp, "wb")
        h_frm.write(self._serialiser.dumps(obj))
        h_frm.flush()
        os.fsync(h_frm.fileno())
        h_frm.close()
        os.replace(xlog_path_tmp, xlog_path)
        assert os.path.exists(xlog_path), "Error writing xlog {}".format(xlog_path)

        if self._mp_notify is not None:
            self._mp_notify.put_nowait(True)

        self._unlock()

    def qsize(self) -> int:
        """
        Return queue size.

        :return: int, size of the Queue
        """
        return len(list(os.listdir(self._queue_path)))
