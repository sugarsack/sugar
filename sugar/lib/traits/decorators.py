"""
Traits decorators
"""


def trait(name):
    """
    Decorator sets name of the function that
    provides the key for the traits.

    :return:
    """
    # pylint: disable=R8001,W0212
    def dec(func):
        """
        Decorator function.

        :param func:
        :return:
        """
        def attrset(*args, **kwargs):
            """
            Container for the attributes of the function.

            :param args:
            :param kwargs:
            :return:
            """
            return func(*args, **kwargs)

        attrset._sugar_provides = name
        attrset._sugar_type = "trait"

        return attrset

    return dec
    # pylint: enable=R8001,W0212
