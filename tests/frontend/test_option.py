from frontend.src.option import Option, OptionCollection


def test_option_collection():
    assert set(
        OptionCollection(
            options=[
                Option('Sentences', callback=None),
                Option('Train Vocabulary', callback=None, keyword='vocabulary'),
                Option('Add Vocabulary', callback=None),
                Option('Quit', callback=None)],
            highlight_color='red'
        ).keys()
    ) == {'sentences', 'vocabulary', 'add', 'quit'}