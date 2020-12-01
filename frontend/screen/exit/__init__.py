from backend.utils.module_interfacing import abstractmodulemethod

from . import (
    on_connection_error,
    on_missing_internet,
    regular
)


@abstractmodulemethod(ignore_modules=['_error_exit_screen'])
def __call__():
    pass
