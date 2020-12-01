from frontend.utils import output

from frontend.utils.query._cancelling import CANCELLED
from frontend.utils.query._ops import indicate_erroneous_input
from frontend.utils.query._repetition import relentlessly


INDENTATION = output.column_percentual_indentation(percentage=0.1)


def centered(query_message: str = '') -> str:
    return input(f'{output.centering_indentation(query_message)}{query_message}')


YES_NO_QUERY_OUTPUT = '(Yes)/(N)o'
YES = 'yes'
YES_NO_OPTIONS = [YES, 'no']

