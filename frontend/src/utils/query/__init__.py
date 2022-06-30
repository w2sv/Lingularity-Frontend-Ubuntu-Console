from frontend.src.utils import output


PROMPT_INDENTATION = output.column_percentual_indentation(percentage=0.1)


def centered(query_message: str = '') -> str:
    return input(f'{output.centering_indentation(query_message)}{query_message}')


YES_NO_QUERY_OUTPUT = '(Yes)/(N)o'
YES = 'yes'
YES_NO_OPTIONS = [YES, 'no']