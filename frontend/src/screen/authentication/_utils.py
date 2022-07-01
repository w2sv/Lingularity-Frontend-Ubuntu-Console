from frontend.src.utils import output


VERTICAL_INDENTATION = output.row_percentual_indentation(percentage=0.15)
HORIZONTAL_INDENTATION = output.column_percentual_indentation(percentage=0.4)


def authentication_screen(func):
    def wrapper(*args, **kwargs):
        print(VERTICAL_INDENTATION)
        return func(*args, **kwargs)
    return wrapper
