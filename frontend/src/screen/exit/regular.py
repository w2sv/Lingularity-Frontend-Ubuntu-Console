import datetime

from frontend.src.screen import _ops
from frontend.src.utils import view
from frontend.src.utils.view import terminal


def _day_of_the_month() -> int:
    return int(datetime.datetime.today().strftime('%d'))


@view.creator(title=terminal.DEFAULT_TERMINAL_TITLE, banner_args=(['lingularity/slant-relief', 'lingularity/sub-zero'][_day_of_the_month() % 2], 'cyan'))
def __call__():
    _ops.display_signum()
    _ops.display_sentence_data_reference()
