from frontend.utils import view, output


@view.view_creator(banner='lingularity/isometric2')
def __call__():
    print(output.row_percentual_indentation(0.2))

    output.centered_print("All requested inputs may be entered in lowercase, as well as merely "
                          "up to a point, which allows for an unambiguous identification of the "
                          "intended choice amongst the respectively eligible options,")
    output.centered_print("e.g. the input of 'it' suffices for selecting Italian since there's "
                          "no other eligible language starting on 'it'", '\n' * 2)

    output.centered_print('HIT ENTER TO PROCEED', end='')

    input()
