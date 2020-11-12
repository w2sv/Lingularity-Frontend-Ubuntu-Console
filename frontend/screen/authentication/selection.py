from frontend.utils import query, output, view
from frontend.screen.authentication import login, sign_up, _utils


_SELECTION_2_SCREEN = {
    'log in': login,
    'sign up': sign_up
}


@view.creator(title=view.DEFAULT_TITLE, banner='lingularity/isometric2', banner_color='blue')
def __call__():
    print(_utils.compute_vertical_indentation())

    output.centered('(L)og in/(S)ign Up')
    selection = query.relentlessly('', options=['log in', 'sign up'], indentation_percentage=0.5)
    return _SELECTION_2_SCREEN[selection].__call__()
