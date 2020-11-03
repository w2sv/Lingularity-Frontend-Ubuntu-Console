from . import ops
from frontend.utils import view


@view.view_creator(banner='lingularity/sub-zero', banner_color='cyan')
def __call__():
    ops.display_signum()
    ops.display_sentence_data_reference()
