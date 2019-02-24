# coding: utf-8
"""
Persistent Queue
"""

from sugar.lib.perq.fsqueue import FSQueue  # noqa


class QueueFactory:
    """
    Queue Factory
    """
    @staticmethod
    def fs_queue(path) -> FSQueue:
        """
        Create FS queue object.

        :param path: xlog storage
        :return: FSQueue instance
        """
        return FSQueue(path=path)
