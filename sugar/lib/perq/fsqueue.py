# coding: utf-8
"""
File-system queue.
"""

from sugar.lib.perq.queue import Queue


class FSQueue(Queue):
    """
    File-system queue
    """
    def empty(self) -> bool:
        """
        Returns True if queue is empty.
        """

    def full(self) -> bool:
        """
        Returns True if queue is full.
        """

    def get(self):
        """
        Blocking get.
        """

    def get_nowait(self):
        """
        Non-blocking get.
        """

    def put(self, obj):
        """
        Blocking put.
        """

    def put_nowait(self, obj):
        """
        Non-blocking put.
        """

    def qsize(self) -> int:
        """
        Return queue size.
        """
