from backend.database import instantiate_client

from frontend import screen
from frontend.reentrypoint import ReentryPoint
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend
)


def __call__():
    is_new_user = screen.login.__call__()

    if is_new_user:
        screen.post_signup_information.__call__()
        screen.language_addition.__call__()

    elif reentry_point := screen.home.__call__():
        return reentry_at(reentry_point)

    return reentry_at(reentry_point=screen.training_selection.__call__(is_new_user=is_new_user))


def reentry_at(reentry_point: ReentryPoint):
    if reentry_point is ReentryPoint.Login:
        screen.login.remove_user_from_disk()
        return __call__()

    elif reentry_point is ReentryPoint.Exit:
        return screen.exit.__call__()

    else:
        if reentry_point is ReentryPoint.LanguageAddition:
            screen.language_addition.__call__()

        elif reentry_point is ReentryPoint.Home:

            if reentry_point := screen.home.__call__():
                return reentry_at(reentry_point=reentry_point)

        return reentry_at(reentry_point=screen.training_selection.__call__())


if __name__ == '__main__':
    screen.ops.maximize_console()

    if not instantiate_client():
        screen.missing_internet_exit.__call__()

    __call__()
