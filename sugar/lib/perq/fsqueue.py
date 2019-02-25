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
    File-system queue.
    """
    # No fcntl here for locking, as it is Unix-only. :-(
    F_LOCK = ".lock"  # Lock file
    MAX_SIZE = 0xfff  # Default max size of the queue
    POLL = 5          # Poll seconds

    def __init__(self, path, maxsize: int = MAX_SIZE, poll: int = POLL):
        self._queue_path = path
        self._max_size = maxsize
        self._xpad = len(str(self._max_size))
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

    def _is_locked(self) -> bool:
        """
        Return True if Queue is locked.
        :return: boolean
        """
        lock_path = os.path.join(self._queue_path, self.F_LOCK)
        try:
            with sugar.utils.files.fopen(lock_path, "rb") as flock:
                locked = flock.read()
        except Exception as exc:
            locked = None

        return bool(locked)

    def _lock(self) -> None:
        """
        Lock mutex of the FS

        :return: None
        """
        lock_path = os.path.join(self._queue_path, self.F_LOCK)
        while True:
            try:
                with sugar.utils.files.fopen(lock_path, "rb") as flock:
                    flock.read()
                time.sleep(0.1)
            except Exception as exc:
                flock = sugar.utils.files.fopen(lock_path, "wb")
                flock.write(str(os.getpid()).encode("ascii"))
                flock.flush()
                os.fsync(flock.fileno())
                flock.close()
                break

    def _unlock(self) -> None:
        """
        Unlock mutex of the FS.

        :return: None
        """
        try:
            os.unlink(os.path.join(self._queue_path, self.F_LOCK))
        except FileNotFoundError:
            pass

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

    def get(self, force=False):
        """
        Get an object in blocking mode.

        :return: object
        """
        return self.__get(wait=True, force=force)

    def get_nowait(self, force=False):
        """
        Get an object in non-blocking mode.

        :return: object
        """
        return self.__get(force=force)

    def __get(self, wait: bool = False, force: bool = False):
        if force:
            self._unlock()

        self._lock()
        if wait:
            if self._mp_notify is not None:
                # Use notification protocol
                self._mp_notify.get()
            else:
                # Poll the disk
                while True:
                    if bool(self._f_xlog()):
                        break
                    time.sleep(self._poll)

        xlog = self._f_dealloc()
        if xlog is None:
            self._unlock()
            raise QueueEmpty("Queue is empty")

        frame_log = os.path.join(self._queue_path, "{}.xlog".format(xlog))
        h_frm = sugar.utils.files.fopen(frame_log, "rb")
        obj = self._serialiser.load(h_frm)
        h_frm.flush()
        h_frm.close()
        os.unlink(frame_log)
        self._unlock()

        return obj

    def _f_xlog(self) -> list:
        """
        Return xlog files.
        :return: list
        """
        xlog = []
        for fname in os.listdir(self._queue_path):
            if fname == self.F_LOCK:
                continue
            xlog.append(int(fname.split(".")[0]))

        return xlog

    def _f_dealloc(self) -> str:
        """
        Deallocate xlog frame.

        :return: name of the previous xlog frame
        """
        frn = self._f_xlog()
        return str(min(frn)).zfill(self._xpad) if frn else None

    def _f_alloc(self) -> str:
        """
        Allocate next xlog frame.

        :return: name of the next xlog frame
        """
        return str(max(self._f_xlog() + [0]) + 1).zfill(self._xpad)

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

    def qsize(self) -> int:
        """
        Return queue size.

        :return: int, size of the Queue
        """
        return len(list(self._f_xlog()))
