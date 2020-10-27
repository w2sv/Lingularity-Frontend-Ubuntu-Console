from typing import Optional

from lingularity.backend.database import MongoDBClient
from lingularity.backend.resources import strings as string_resources

from .ops.reference_language import query_english_reference_language
from lingularity.frontend.console.utils import view, output, input_resolution
from lingularity.frontend.console.screen import ops
from lingularity.frontend.console.state import State
from lingularity.frontend.console.reentrypoint import ReentryPoint


@view.view_creator(title='Home', banner_kind='impossible', banner_color='red')
def __call__() -> Optional[ReentryPoint]:
    """ Returns:
            return_to_language_addition_flag: bool """

    trained_languages = MongoDBClient.get_instance().query_trained_languages()

    train_english = False

    output.centered_print("YOUR LANGUAGES:\n")
    for language_group in output.group_by_starting_letter(trained_languages, is_sorted=False):
        output.centered_print('  '.join(language_group))

    OPTION_2_REENTRY_POINT = {
        'sign': ReentryPoint.Login,
        'add': ReentryPoint.LanguageAddition,
        'exit': ReentryPoint.Exit
    }

    option_keywords = list(OPTION_2_REENTRY_POINT.keys())

    output.centered_print(f"\nAdditional Options: "
                          f"{output.INTER_OPTION_INDENTATION}(A)dd Language"
                          f"{output.INTER_OPTION_INDENTATION}(S)ign Out"
                          f"{output.INTER_OPTION_INDENTATION}(E)xit Program\n")

    selection = input_resolution.query_relentlessly(query_message='Select Language/Option: ', options=trained_languages + option_keywords)

    if selection in option_keywords:
        return OPTION_2_REENTRY_POINT[selection]

    if selection == string_resources.ENGLISH:
        train_english = True
        selection = query_english_reference_language()

    State.set_language(non_english_language=selection, train_english=train_english)

    return None
