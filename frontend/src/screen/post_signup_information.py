from frontend.src.utils import output, query
from frontend.src.utils import view


@view.creator(title='General Usage Information', banner_args=('lingularity/isometric2', 'grey'))
def __call__():
    print(output.row_percentual_indentation(0.15))

    INFORMATION_BLOCK = ("All requested inputs may be entered in lowercase, as well as merely",
                         "up to a point allowing for an unambiguous identification of the ",
                         "intended choice amongst the respectively eligible options.",
                         "E.g. the input of 'it' suffices for selecting Italian since there's ",
                         "no other eligible language starting on 'it'")

    INDENTATION = output.block_centering_indentation(INFORMATION_BLOCK)
    for row in INFORMATION_BLOCK:
        print(f'{INDENTATION}{row}')
    print(view.VERTICAL_OFFSET)

    output.centered('HIT ENTER TO PROCEED')
    query.centered()
