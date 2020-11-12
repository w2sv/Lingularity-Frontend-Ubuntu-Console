from . import ops
from frontend.utils import view


@view.creator(title=view.DEFAULT_TITLE, banner='lingularity/sub-zero', banner_color='cyan')
def __call__():
    ops.display_signum()
    ops.display_sentence_data_reference()
