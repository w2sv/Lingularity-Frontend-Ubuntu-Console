from functools import wraps

from lingularity.frontend.console.utils.output import clear_screen, DEFAULT_VERTICAL_VIEW_OFFSET


def creates_new_view(function):
    """ Decorator for functions creating new terminal view,
        serving both documentation purposes as well as initializing new view
        by clearing screen and outputting vertical offset """

    @wraps(function)
    def wrapper(*args, **kwargs):
        clear_screen()
        print(DEFAULT_VERTICAL_VIEW_OFFSET)

        return function(*args, **kwargs)
    return wrapper
