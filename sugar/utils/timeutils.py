# coding: utf-8
"""
Date/time utils.
"""

import datetime
import pytz


def to_iso(dtm: datetime.datetime) -> str:
    """
    Date/time to ISO format.

    :param dtm: date/time object.
    :return: ISO format with UTC zone
    """
    if dtm.tzinfo is None:
        dtm = pytz.utc.localize(dtm)

    return dtm.isoformat()


def from_iso(dtm: str) -> datetime.datetime:
    """
    Date/time in ISO format to datetime object.

    :param dtm: date/time string in ISO format
    :return: datetime object.
    """
    if ":" == dtm[-3:-2]:
        dtm = dtm[:-3] + dtm[-2:]
    else:
        dtm += "+0000"

    return datetime.datetime.strptime(dtm, "%Y-%m-%dT%H:%M:%S.%f%z")
