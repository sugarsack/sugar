# coding: utf-8
"""
Jobstore const.
"""


class JobTypes:
    """
    Job types struct.
    """
    RUNNER = "runner"
    STATE = "state"

    @classmethod
    def validate(cls, job_type: str) -> None:
        """
        Raise assertion error if job type is unknown.

        :param job_type: one of runner or state.
        :return: None
        """
        assert job_type in [cls.RUNNER, cls.STATE]
