from frontend.utils import output


def compute_vertical_indentation() -> str:
    return output.row_percentual_indentation(percentage=0.15)


def compute_horizontal_indentation() -> str:
    return output.column_percentual_indentation(percentage=0.4)
