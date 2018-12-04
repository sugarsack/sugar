import logging
import sys


def setup_logger():
    """
    Setup logger to the app.

    :return:
    """
    level = logging.NOTSET
    root = logging.getLogger()
    root.setLevel(level)

    handlers = []
    handlers.append(logging.StreamHandler(sys.stdout))

    for handler in handlers:
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)
