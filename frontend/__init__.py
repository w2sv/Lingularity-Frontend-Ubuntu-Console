import subprocess

subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'])  # maximize terminal, DON'T ALTER THE POSITION OF THIS LINE

from frontend import screen
from frontend import locally_cashed_user
from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend
)


def __call__():
    """ Program entry point

        Triggers authentication and consecutively invokes procedure depending
        on whether or not account has just been created """

    screen.authentication.__call__()

    # display post signup information, reentry at language addition
    # in case of new user, otherwise proceed directly to home screen
    # of locally cached user
    if State.is_new_user:
        screen.post_signup_information.__call__()
        return reentry_at(reentry_point=screen.language_addition.__call__())

    return reentry_at(reentry_point=screen.home.__call__())


def reentry_at(reentry_point: ReentryPoint):
    """ Central menu shifting function

        Kicks off program anew from passed reentry point """

    if reentry_point is ReentryPoint.Login:
        locally_cashed_user.remove()
        return __call__()

    elif reentry_point is ReentryPoint.LanguageAddition:
        return reentry_at(reentry_point=screen.language_addition.__call__())

    elif reentry_point is ReentryPoint.Home:
        return reentry_at(reentry_point=screen.home.__call__())

    elif reentry_point is ReentryPoint.TrainingSelection:
        return reentry_at(reentry_point=screen.training_selection.__call__())

    elif reentry_point is ReentryPoint.Exit:
        return screen.exit.regular.__call__()


if __name__ == '__main__':
    from pymongo import errors
    from backend.database import instantiate_database_client

    from frontend import logging

    logging.enable_backend_logging()

    # check for pymongo-related, insurmountable initialization errors,
    # invoke corresponding exit screen in case of occurrence, otherwise
    # run program
    if instantiation_error := instantiate_database_client(server_selection_timeout=1_500):
        if instantiation_error is errors.ServerSelectionTimeoutError:
            screen.exit.on_connection_error.__call__()
        elif instantiation_error is errors.ConfigurationError:
            screen.exit.on_missing_internet.__call__()
    else:
        __call__()
