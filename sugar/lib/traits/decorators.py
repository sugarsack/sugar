"""
Traits decorators
"""


def trait(name):
    """
    Decorator sets name of the function that
    provides the key for the traits.

    :return:
    """
    def dec(f):
        def attrset(*args, **kwargs):
            return f(*args, **kwargs)
        attrset._sugar_provides = name
        attrset._sugar_type = "trait"
        return attrset
    return dec
