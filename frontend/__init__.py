import subprocess
subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'])

from frontend import screen
from frontend import locally_cashed_user
from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.utils.view import terminal
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend
)


def __call__():
    screen.authentication.__call__()

    if State.is_new_user:
        screen.post_signup_information.__call__()
        return reentry_at(reentry_point=screen.language_addition.__call__())
    return reentry_at(reentry_point=screen.home.__call__())


def reentry_at(reentry_point: ReentryPoint):
    if reentry_point is ReentryPoint.Login:
        locally_cashed_user.remove()
        return __call__()

    elif reentry_point is ReentryPoint.Exit:
        return screen.exit.__call__()

    elif reentry_point is ReentryPoint.LanguageAddition:
        return reentry_at(screen.language_addition.__call__())

    elif reentry_point is ReentryPoint.Home:
        return reentry_at(reentry_point=screen.home.__call__())

    return reentry_at(reentry_point=screen.training_selection.__call__())


if __name__ == '__main__':
    from pymongo import errors

    from backend.database import instantiate_client
    from . import logging

    if instantiation_error := instantiate_client():
        print(instantiation_error)
        if instantiation_error is errors.ServerSelectionTimeoutError:
            screen.connection_error_exit.__call__()
        else:  # errors.ConfigurationError
            screen.missing_internet_exit.__call__()

    else:
        __call__()
