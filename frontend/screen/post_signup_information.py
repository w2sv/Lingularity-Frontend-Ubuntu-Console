from frontend.utils import view, output


@view.creator(banner='lingularity/isometric2')
def __call__():
    print(output.row_percentual_indentation(0.2))

    output.centered("All requested inputs may be entered in lowercase, as well as merely "
                          "up to a point, which allows for an unambiguous identification of the "
                          "intended choice amongst the respectively eligible options,")
    output.centered("e.g. the input of 'it' suffices for selecting Italian since there's "
                          "no other eligible language starting on 'it'", '\n' * 2)

    output.centered('HIT ENTER TO PROCEED', end='')

    input()
