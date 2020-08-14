import pytest

from lingularity.backend.data_fetching.sentence_data import SentenceDataFetcher
from lingularity.backend.data_fetching.demonyms import fetch_demonyms
from lingularity.backend.data_fetching.language_typical_forenames import _fetch_countries_language_officially_employed_in


def test_zip_download_link_parsing():
    content_retriever = SentenceDataFetcher()
    assert all(k.endswith('.zip') for k in content_retriever.language_2_ziplink.values())

    # check if number of languages has changed
    if (n_languages := len(content_retriever.language_2_ziplink)) != 79:
        print(f'# of available languages has changed: {n_languages}')


@pytest.mark.parametrize('country,expected_demonyms', [
    ('USA', ['American']),
    ('France', ['French']),
    ('Hungary', ['Hungarian']),
    ('Germany', ['German']),
    ('Russia', ['Russian']),
    ('Turkmenistan', ['Turkmenistani', 'Turkmen']),
    ('Sweden', ['Swedish', 'Swede']),
    ('Spain', ['Spanish', 'Spaniard']),
    ('Australia', ['Australian']),
    ('Israel', ['Israeli']),
    ('Serbia', ['Serbian']),
    ('Austria', ['Austrian']),
    ('Monaco', ['Monégasque', 'Monacan']),
    ('Uzbekistan', ['Uzbek']),
    ('Indogermanic', [])
])
def test_demonyms_fetching(country, expected_demonyms):
    assert list(fetch_demonyms(country)) == expected_demonyms


@pytest.mark.parametrize('language,expected_countries', [
    ('French', ['Belgium', 'Benin', 'Burkina Faso', 'Burundi', 'Cameroon', 'Canada', 'Central African Republic', 'Chad', 'Comoros', 'Congo', 'DR Congo', 'Djibouti', 'Equatorial Guinea', 'France', 'Gabon', 'Guinea', 'Haiti', 'Ivory Coast', 'Luxembourg', 'Madagascar', 'Mali', 'Monaco', 'Niger', 'Rwanda', 'Senegal', 'Seychelles', 'Switzerland', 'Togo', 'Vanuatu']),
    ('Spanish', ['Argentina', 'Bolivia', 'Chile', 'Colombia', 'Costa Rica', 'Cuba', 'Dominican Republic', 'Ecuador', 'El Salvador', 'Equatorial Guinea', 'Guatemala', 'Honduras', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay', 'Peru', 'Spain', 'Uruguay', 'Venezuela']),
    ('Russian', ['Russia', 'Belarus', 'Kazakhstan', 'Kyrgyzstan', 'Tajikistan', 'Uzbekistan', 'Ukraine', 'Autonomous Republic of Crimea', 'Turkmenistan', 'Moldova', 'Gagauzia', 'Transnistria']),
    ('German', ['Austria', 'Belgium', 'Germany', 'Liechtenstein', 'Luxembourg', 'Switzerland']),
    ('Chinese', ['China']),
    ('Japanese', ['Japan']),
    ('Korean', ['South_Korea', 'Russia', 'China', 'North_Korea']),
    ('Hebrew', ['Israel']),
    ('Urdu', ['Pakistan']),
    ('Pashto', ['Afghanistan']),
    ('Tagalog', ['Philippines']),
    ('Waray', None),
    ('Arabic', ['Algeria']),
    ('Hungarian', ['Hungary', 'Croatia', 'Vojvodina', 'Austria', 'Serbia', 'Europe', 'Slovakia', 'Slovenia', 'Ukraine', 'Romania']),
    ('Serbian', ['Bosnia_and_Herzegovina', 'Hungary', 'Croatia', 'North_Macedonia', 'Serbia', 'Slovakia', 'Kosovo', 'Montenegro', 'Romania', 'Czech_Republic']),
])
def test_language_corresponding_countries_fetching(language, expected_countries):
    if hasattr(expected_countries, '__iter__'):
        assert set(_fetch_countries_language_officially_employed_in(language) + expected_countries).__len__() == expected_countries.__len__()
    else:
        assert _fetch_countries_language_officially_employed_in(language) == expected_countries