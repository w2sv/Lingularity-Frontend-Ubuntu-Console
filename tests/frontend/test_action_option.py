from frontend.src.screen.action_option import Option, Options


def test_action_options():
    assert Options(
        options=[
            Option('Translate Sentences', keyword_index=1, callback=None),
            Option('Train Vocabulary', keyword_index=1, callback=None),
            Option('Add Vocabulary', keyword_index=0, callback=None),
            Option('Quit', callback=None)],
        color='red'
    ).keywords == []