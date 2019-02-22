# coding: utf-8
"""
Persistent Queue.
"""
import abc


class Queue(abc.ABC):
    """
    Queue class
    """

    @abc.abstractmethod
    def empty(self) -> bool:
        """
        Returns True if queue is empty.
        """

    @abc.abstractmethod
    def full(self) -> bool:
        """
        Returns True if queue is full.
        """

    @abc.abstractmethod
    def get(self):
        """
        Blocking get.
        """

    @abc.abstractmethod
    def get_nowait(self):
        """
        Non-blocking get.
        """

    @abc.abstractmethod
    def put(self):
        """
        Blocking put.
        """

    @abc.abstractmethod
    def put_nowait(self):
        """
        Non-blocking put.
        """

    @abc.abstractmethod
    def qsize(self) -> int:
        """
        Return queue size.
        """
