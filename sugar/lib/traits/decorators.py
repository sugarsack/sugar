"""
Traits decorators
"""


def trait(name):
    """
    Decorator sets name of the function that
    provides the key for the traits.

    :param name: name of the provided trait
    :return: Decorated trait
    """
    # pylint: disable=W0212
    def dec(func):
        """
        Decorator function.

        :param func: function of the trait
        :return: wrapper function
        """
        def attrset(*args, **kwargs):
            """
            Container for the attributes of the function.

            :param args: arguments of the trait function
            :param kwargs: keyword arguments of the trait function
            :return: result of the trait function
            """
            return func(*args, **kwargs)

        attrset._sugar_provides = name
        attrset._sugar_type = "trait"

        return attrset

    return dec
    # pylint: enable=W0212
