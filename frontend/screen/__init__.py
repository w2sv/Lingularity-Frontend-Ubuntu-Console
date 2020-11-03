from backend.utils.module_abstraction import abstractmodulemethod

from . import (
    login,
    home,
    training_selection,
    post_signup_information,
    missing_internet_exit,
    language_addition,
    exit
)


@abstractmodulemethod
def __call__():
    pass
