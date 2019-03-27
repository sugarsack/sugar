# coding: utf-8
"""
Job storage stats.
"""


class JobStats:
    """
    Stats of the job task.
    """
    def __init__(self, **kwargs):
        self.jid = kwargs.get("jid")
        self.tasks = kwargs.get("tasks", 0)
        self.finished = kwargs.get("finished", 0)

    @property
    def percent(self) -> int:
        """
        Get percentage of done tasks.

        :return: int
        """
        return int(self.finished / self.tasks * 100)
