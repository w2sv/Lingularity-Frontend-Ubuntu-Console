from backend.database import instantiate_client

from frontend import screen
from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend
)


def __call__():
    screen.login.__call__()

    if State.is_new_user:
        screen.post_signup_information.__call__()
        screen.language_addition.__call__()

    return reentry_at(reentry_point=screen.home.__call__())


def reentry_at(reentry_point: ReentryPoint):
    if reentry_point is ReentryPoint.Login:
        screen.login.remove_user_from_disk()
        return __call__()

    elif reentry_point is ReentryPoint.Exit:
        return screen.exit.__call__()

    elif reentry_point is ReentryPoint.LanguageAddition:
        screen.language_addition.__call__()

    elif reentry_point is ReentryPoint.Home:
        return reentry_at(reentry_point=screen.home.__call__())

    return reentry_at(reentry_point=screen.training_selection.__call__())


if __name__ == '__main__':
    from backend.logging import enable_backend_logging
    import os

    enable_backend_logging(file_path=f'{os.getcwd()}/logging.txt')

    screen.ops.maximize_console()

    if not instantiate_client():
        screen.missing_internet_exit.__call__()

    __call__()
