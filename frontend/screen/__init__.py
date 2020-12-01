from backend.utils.module_interfacing import abstractmodulemethod

from . import (
    authentication,
    home,
    training_selection,
    post_signup_information,
    language_addition,
    exit,
    account_deletion
)


@abstractmodulemethod(ignore_modules=['_action_option', '_ops'])
def __call__():
    pass
