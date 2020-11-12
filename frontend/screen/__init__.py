from backend.utils.module_interfacing import abstractmodulemethod

from . import (
    authentication,
    home,
    training_selection,
    post_signup_information,
    missing_internet_exit,
    language_addition,
    exit,
    account_deletion
)


@abstractmodulemethod
def __call__():
    pass
