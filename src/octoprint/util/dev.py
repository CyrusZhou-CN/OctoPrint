"""
This module provides a bunch of utility methods and helpers FOR DEVELOPMENT ONLY.
"""

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"

import contextlib
import time


@contextlib.contextmanager
def duration_log(context=None, log=None):
    """
    Context manager to log the duration of the wrapped code block.

    If no ``log`` function is provided will use a ``debug`` python logger for
    ``octoprint.util.dev``.

    ``context`` can be set to give some textual context in the output.

    Arguments:
        context (str): A custom string to give some textual context in the output.
        log (callable): The log function to use to log the execution duration.
    """
    if log is None:
        import logging

        log = logging.getLogger(__name__).debug

    start = time.monotonic()
    try:
        yield
    finally:
        end = time.monotonic()
        duration = end - start

        if context:
            message = "Execution of {name} took {duration}s"
        else:
            message = "Execution of codeblock took {duration}s"

        log(message.format(name=context, duration=duration))


def log_duration(log=None, with_args=False):
    """
    Decorator that logs the execution duration of the annotated function.

    Arguments:
        log (callable): The logging function to use.
        with_args (bool): Whether to include the calling arguments in the logged
            output or not.
    """

    def decorator(f):
        def wrapped(*args, **kwargs):
            if with_args:
                args_str = ", ".join(repr(x) for x in args)
                kwargs_str = ", ".join(
                    f"{item[0]}={repr(item[1])}" for item in kwargs.items()
                )
                sep = ", " if args_str and kwargs_str else ""
                arguments = "".join([args_str, sep, kwargs_str])
            else:
                arguments = "..."
            context = f"{f.__name__}({arguments})"
            with duration_log(context=context, log=log):
                return f(*args, **kwargs)

        return wrapped

    return decorator
