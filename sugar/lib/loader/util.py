# coding: utf-8
"""
Loader utilities: decorators etc.
"""

import sugar.utils.absmod
import sugar.lib.exceptions


def guard(func):
    """
    Guard call.

    :param func: method or function to be guarded by the result object.
    :return: wrapper function
    """
    def caller(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            result = sugar.utils.absmod.ActionResult()
            result.error = str(exc)
            result.errcode = sugar.lib.exceptions.SugarException.get_errcode(exc)
        return result

    return caller
