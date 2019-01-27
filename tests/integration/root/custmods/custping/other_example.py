# coding: utf-8
"""
Example custom module.
"""

def ping(name=None):
    """
    Custom pingpong
    """
    return {"text": "{}".format(name or "pong")}
