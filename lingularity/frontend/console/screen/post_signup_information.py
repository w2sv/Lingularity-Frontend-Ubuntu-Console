from lingularity.frontend.console.utils import output, view


@view.view_creator()
def __call__():
    print(view.DEFAULT_VERTICAL_VIEW_OFFSET)

    output.centered_print("All requested inputs may be entered in lowercase, as well as merely up to a reentry_point, which allows for an unambigious identification of the intended choice amongst the respectively possible options,")
    output.centered_print("e.g. the input of 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n' * 2)
    output.centered_print('Hit Enter to proceed', end='')

    input()
