from frontend.src.utils import output, prompt
from frontend.src.utils import view
from frontend.src.utils.output.percentual_indenting import IndentedPrint
from frontend.src.utils.view import Banner


@view.creator(
    title='General Usage Information',
    banner=Banner('lingularity/isometric2', 'grey'),
    additional_vertical_offset=output.row_percentual_indentation(0.15)
)
def __call__():
    INFORMATION_BLOCK = ("All requested inputs may be entered in lowercase, as well as merely",
                         "up to a point allowing for an unambiguous identification of the ",
                         "intended choice amongst the respectively eligible options.",
                         "E.g. the input of 'it' suffices for selecting Italian since there's ",
                         "no other eligible language starting on 'it'")

    _print = IndentedPrint(indentation=output.block_centering_indentation(INFORMATION_BLOCK))
    for row in INFORMATION_BLOCK:
        _print(row)
    print(view.VERTICAL_OFFSET)

    output.centered('HIT ENTER TO PROCEED')
    prompt.centered()
