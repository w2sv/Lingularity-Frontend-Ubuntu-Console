import datetime

from . import ops
from frontend.utils import view


def _day_of_the_month() -> int:
    return int(datetime.datetime.today().strftime('%d'))


@view.creator(title=view.DEFAULT_TITLE, banner_args=(['lingularity/slant-relief', 'lingularity/sub-zero'][_day_of_the_month() % 2], 'cyan'))
def __call__():
    ops.display_signum()
    ops.display_sentence_data_reference()
