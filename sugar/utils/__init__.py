import logging
import sys


LOG_LEVELS = {
    'all': logging.NOTSET,
    'debug': logging.DEBUG,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'fatal': logging.FATAL
}


def setup_logger(current_level):
    """
    Setup logger to the app.

    :return:
    """
    level = LOG_LEVELS.get(current_level, LOG_LEVELS['info'])
    root = logging.getLogger()
    root.setLevel(level)

    handlers = []
    handlers.append(logging.StreamHandler(sys.stdout))

    for handler in handlers:
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)
