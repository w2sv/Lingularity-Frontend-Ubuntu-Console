import time
from functools import wraps

from frontend.src.utils import view


def error_exit_screen(func):
    """ Decorator for error exit screen invocation function
        printing vertical view offset and sleeping for some
        seconds after execution of the decorated function """

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        print(view.VERTICAL_OFFSET)
        time.sleep(5)
        return res
    return wrapper
