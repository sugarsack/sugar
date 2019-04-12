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
    def pending(self) -> bool:
        """
        Returns True if anything is in the notification layer.

        :return: bool
        """

    @abc.abstractmethod
    def empty(self) -> bool:
        """
        Returns True if queue is empty.

        :return: bool
        """

    @abc.abstractmethod
    def full(self) -> bool:
        """
        Returns True if queue is full.

        :return: bool
        """

    @abc.abstractmethod
    def get(self, force: bool):
        """
        Blocking get.

        :param force: force lock removal
        :return: obj
        """

    @abc.abstractmethod
    def get_nowait(self, force: bool):
        """
        Non-blocking get.

        :param force: force lock removal
        :return: obj
        """

    @abc.abstractmethod
    def put(self, obj) -> None:
        """
        Blocking put.

        :param obj: object to put
        :return: None
        """

    @abc.abstractmethod
    def put_nowait(self, obj) -> None:
        """
        Non-blocking put.

        :param obj: object to put
        :return: None
        """

    @abc.abstractmethod
    def qsize(self) -> int:
        """
        Return queue size.

        :return: size
        """
