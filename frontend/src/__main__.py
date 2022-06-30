from pathlib import Path
import subprocess

from pymongo import errors
from backend.src.database import connect_database_client
from backend.src.logging import enable_backend_logging

# maximize terminal window, line position not to be altered
subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'])

from frontend.src import logged_in_user, screen
from frontend.src.state import State
from frontend.src.reentrypoint import ReentryPoint


def __call__():
    """ Program entry point

        Triggers authentication and consecutively invokes procedure depending
        on whether account has just been created """

    screen.authentication.__call__()

    # display post signup information, reentry at language addition
    # in case of new user, otherwise proceed directly to home screen
    # of locally cached user
    if State.instance().is_new_user:
        screen.post_signup_information.__call__()
        return reentry_at(reentry_point=screen.language_addition.__call__())
    return reentry_at(reentry_point=screen.home.__call__())


def reentry_at(reentry_point: ReentryPoint):
    """ Central menu shifting function

        Kicks off program anew from passed reentry point """

    if reentry_point is ReentryPoint.Login:
        logged_in_user.remove()
        return __call__()

    elif reentry_point is ReentryPoint.LanguageAddition:
        return reentry_at(reentry_point=screen.language_addition.__call__())

    elif reentry_point is ReentryPoint.Home:
        return reentry_at(reentry_point=screen.home.__call__())

    elif reentry_point is ReentryPoint.TrainingSelection:
        return reentry_at(reentry_point=screen.training_selection.__call__())

    elif reentry_point is ReentryPoint.Exit:
        return screen.exit.regular.__call__()


enable_backend_logging(file_path=Path.cwd() / 'logging.txt')

# check for pymongo-related, insurmountable initialization errors,
# invoke corresponding exit screen in case of occurrence, otherwise
# run program
if instantiation_error := connect_database_client(server_selection_timeout=1_500):
    if instantiation_error is errors.ServerSelectionTimeoutError:
        screen.exit.on_connection_error.__call__()
    elif instantiation_error is errors.ConfigurationError:
        screen.exit.on_missing_internet.__call__()
else:
    __call__()
