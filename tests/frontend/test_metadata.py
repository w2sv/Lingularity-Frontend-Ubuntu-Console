from frontend.src.metadata import country_metadata, main_country_flag


def test_country_metadata():
    assert len(country_metadata) == 258


def test_main_country_flag():
    assert main_country_flag('French') == '🇫🇷'