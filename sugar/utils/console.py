"""
CLI console
"""


def get_yn_input(prompt):
    """
    Get Yes/No prompt answer.

    :param prompt:
    :return:
    """

    a = None
    while a not in ["y", "n", ""]:
        a = (input(prompt + " (y/N): ") or "").lower() or "n"

    return a == "y"
