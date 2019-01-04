"""
CLI console
"""


def get_yn_input(prompt):
    """
    Get Yes/No prompt answer.

    :param prompt: string prompt
    :return: bool
    """

    answer = None
    while answer not in ["y", "n", ""]:
        answer = (input(prompt + " (y/N): ") or "").lower() or "n"

    return answer == "y"
