# coding: utf-8
"""
Functions for creating and working with job IDs
"""
from __future__ import absolute_import, print_function, unicode_literals

from calendar import month_abbr as months
import datetime
import os

from sugar.lib import six
from sugar.utils.objects import Singleton

# pylint: disable=C0103

@Singleton
class __JobID(object):
    """
    Job ID global container.
    """

    def __init__(self):
        self.__last_jid = None

    def create(self):
        """
        Generate a Job ID (jid)
        """

        jid_dt = datetime.datetime.now()
        if self.__last_jid is not None and self.__last_jid >= jid_dt:
            jid_dt = self.__last_jid + datetime.timedelta(microseconds=1)
        self.__last_jid = jid_dt

        return '{0:%Y%m%d%H%M%S%f}_{1}'.format(jid_dt, os.getpid())

    @staticmethod
    def is_jid(jid):
        """
        Returns True if the passed in value is a job id.

        :param jid:
        :return:
        """
        ret = False
        jid = six.text_type(jid)
        if len(jid) > 21 and jid[21] == '_':
            try:
                jid, pid = jid.split('_', 1)
                ret = int(jid) and int(pid)  # Pid cannot be 0.
            except ValueError:
                pass

        return ret

    def get_pid(self, jid):
        """
        Get PID from Jid.

        :param jid:
        :return:
        """
        if self.is_jid(jid):
            pid = int(jid.split('_', 1)[-1])
        else:
            pid = -1

        return pid

    @staticmethod
    def to_time(jid):
        """
        Convert a Sugar Job ID into the time when the job was invoked.

        :param jid:
        :return:
        """
        jid = six.text_type(jid)
        if len(jid) > 21  and jid[21] == '_':
            ret = '{0}, {1} {2} {3}:{4}:{5}.{6}'.format(jid[:4], months[int(jid[4:6])], jid[6:8],
                                                        jid[8:10], jid[10:12], jid[12:14], jid[14:20])
        else:
            ret = ''

        return ret


jidstore = __JobID()
