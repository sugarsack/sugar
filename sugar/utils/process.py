# coding: utf-8
"""
Daemons
"""

# Import python libs
from __future__ import absolute_import, with_statement, print_function, unicode_literals
import sys
import signal
import contextlib
import subprocess
import multiprocessing
import multiprocessing.util

import sugar.utils.exitcodes
from sugar.lib.logger.manager import get_logger

log = get_logger(__name__)  # pylint: disable=C0103

# pylint: disable=import-error
HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    pass

try:
    import setproctitle
    HAS_SETPROCTITLE = True
except ImportError:
    HAS_SETPROCTITLE = False


def appendproctitle(name):
    """
    Append 'name' to the current process title
    """
    if HAS_SETPROCTITLE:
        setproctitle.setproctitle(setproctitle.getproctitle() + ' ' + name)


def systemd_notify_call(action):
    """
    Notify call to the systemd.

    :param action:
    :return:
    """
    process = subprocess.Popen(['systemd-notify', action], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()
    status = process.poll()

    return status == 0


class MultiprocessingProcess(multiprocessing.Process):
    """
    Multiprocessing process
    """
    def __new__(cls, *args, **kwargs):
        instance = super(MultiprocessingProcess, cls).__new__(cls)
        # Patch the run method at runtime because decorating the run method
        # with a function with a similar behavior would be ignored once this
        # class'es run method is overridden.
        instance._original_run = instance.run
        instance.run = instance._run
        return instance

    # __setstate__ and __getstate__ are only used on Windows.
    # We do this so that __init__ will be invoked on Windows in the child
    # process so that a register_after_fork() equivalent will work on Windows.
    def __setstate__(self, state):
        self._is_child = True
        args = state['args']
        kwargs = state['kwargs']
        # This will invoke __init__ of the most derived class.
        self.__init__(*args, **kwargs)

    def _run(self):
        try:
            return self._original_run()
        except SystemExit:
            # These are handled by multiprocessing.Process._bootstrap()
            raise
        except Exception as exc:
            log.error("An un-handled exception from the multiprocessing "
                      "process '{}' was caught:\n".format(self.name,))
            raise


class SignalHandlingMultiprocessingProcess(MultiprocessingProcess):
    """
    Signal handling multiprocess
    """
    def __init__(self, *args, **kwargs):
        super(SignalHandlingMultiprocessingProcess, self).__init__(*args, **kwargs)
        multiprocessing.util.register_after_fork(self, SignalHandlingMultiprocessingProcess.__setup_signals)

    def __setup_signals(self):
        signal.signal(signal.SIGINT, self._handle_signals)
        signal.signal(signal.SIGTERM, self._handle_signals)

    def _handle_signals(self, signum, sigframe):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        msg = '{0} received a '.format(self.__class__.__name__)
        if signum == signal.SIGINT:
            msg += 'SIGINT'
        elif signum == signal.SIGTERM:
            msg += 'SIGTERM'
        msg += '. Exiting'
        log.info(msg)
        if HAS_PSUTIL:
            process = psutil.Process(self.pid)
            if hasattr(process, 'children'):
                for child in process.children(recursive=True):
                    if child.is_running():
                        child.terminate()
        sys.exit(sugar.utils.exitcodes.EX_OK)

    def start(self):
        with default_signals(signal.SIGINT, signal.SIGTERM):
            super(SignalHandlingMultiprocessingProcess, self).start()


@contextlib.contextmanager
def default_signals(*signals):
    old_signals = {}
    for signum in signals:
        try:
            old_signals[signum] = signal.getsignal(signum)
            signal.signal(signum, signal.SIG_DFL)
        except ValueError as exc:
            # This happens when a netapi module attempts to run a function
            # using wheel_async, because the process trying to register signals
            # will not be the main PID.
            log.trace(
                'Failed to register signal for signum %d: %s',
                signum, exc
            )

    # Do whatever is needed with the reset signals
    yield

    # Restore signals
    for signum in old_signals:
        signal.signal(signum, old_signals[signum])

    del old_signals
