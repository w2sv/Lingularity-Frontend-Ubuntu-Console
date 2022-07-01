from frontend.src.option import Option, OptionCollection


def test_action_options():
    assert OptionCollection(
        options=[
            Option('Translate Sentences', keyword_index=1, callback=None),
            Option('Train Vocabulary', keyword_index=1, callback=None),
            Option('Add Vocabulary', keyword_index=0, callback=None),
            Option('Quit', callback=None)],
        highlight_color='red'
    ).keywords == ['sentences', 'vocabulary', 'add', 'quit']