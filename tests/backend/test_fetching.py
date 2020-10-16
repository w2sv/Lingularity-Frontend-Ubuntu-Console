import pytest
from collections import Counter

from lingularity.backend.ops.data_mining.scraping import (scrape_sentence_data_download_links, scrape_demonym,
                                                          scrape_popular_forenames, scrape_countries_language_employed_in)


def test_zip_download_link_parsing():
    language_2_download_link = scrape_sentence_data_download_links()
    assert all(k.endswith('.zip') for k in language_2_download_link.values())

    # check if number of languages has changed
    if (n_languages := len(language_2_download_link)) != 79:
        print(f'# of available languages has changed: {n_languages}')


@pytest.mark.parametrize('country,expected_demonym', [
    ('USA', 'American'),
    ('France', 'French'),
    ('Hungary', 'Hungarian'),
    ('Germany', 'German'),
    ('Russia', 'Russian'),
    ('Turkmenistan', 'Turkmenistani'),
    ('Sweden', 'Swede'),
    ('Spain', 'Spanish'),
    ('Australia', 'Australian'),
    ('Israel', 'Israeli'),
    ('Serbia', 'Serbian'),
    ('Austria', 'Austrian'),
    ('Monaco', 'Monacan'),
    ('Uzbekistan', 'Uzbek'),
    ('Indogermanic', None)
])
def test_demonyms_fetching(country, expected_demonym):
    assert scrape_demonym(country) == expected_demonym


@pytest.mark.parametrize('language,expected_countries', [
    ('French', ['Belgium', 'Benin', 'Burkina Faso', 'Burundi', 'Cameroon', 'Canada', 'Central African Republic', 'Chad', 'Comoros', 'Congo', 'DR Congo', 'Djibouti', 'Equatorial Guinea', 'France', 'Gabon', 'Guinea', 'Haiti', 'Ivory Coast', 'Luxembourg', 'Madagascar', 'Mali', 'Monaco', 'Niger', 'Rwanda', 'Senegal', 'Seychelles', 'Switzerland', 'Togo', 'Vanuatu']),
    ('Spanish', ['Argentina', 'Bolivia', 'Chile', 'Colombia', 'Costa Rica', 'Cuba', 'Dominican Republic', 'Ecuador', 'El Salvador', 'Equatorial Guinea', 'Guatemala', 'Honduras', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay', 'Peru', 'Spain', 'Uruguay', 'Venezuela']),
    ('Russian', ['Russia', 'Belarus', 'Kazakhstan', 'Kyrgyzstan', 'Tajikistan', 'Uzbekistan', 'Ukraine', 'Autonomous Republic of Crimea', 'Turkmenistan', 'Moldova', 'Gagauzia', 'Transnistria']),
    ('German', ['Austria', 'Belgium', 'Germany', 'Liechtenstein', 'Luxembourg', 'Switzerland']),
    ('Chinese', ['China']),
    ('Japanese', ['Japan']),
    ('Korean', ['South_Korea', 'Russia', 'China', 'North_Korea']),
    ('Hebrew', ['Israel', 'South_Africa', 'Poland']),
    ('Urdu', ['Pakistan']),
    ('Pashto', ['Afghanistan']),
    ('Tagalog', ['Philippines']),
    ('Waray', None),
    ('Arabic', ['Algeria']),
    ('Hungarian', ['Hungary', 'Croatia', 'Vojvodina', 'Austria', 'Serbia', 'Slovakia', 'Slovenia', 'Ukraine', 'Romania']),
    ('Serbian', ['Bosnia_and_Herzegovina', 'Hungary', 'Croatia', 'North_Macedonia', 'Serbia', 'Slovakia', 'Kosovo', 'Montenegro', 'Romania', 'Czech_Republic']),
])
def test_language_corresponding_countries_fetching(language, expected_countries):
    countries_language_employed_in = scrape_countries_language_employed_in(language)

    if expected_countries is None:
        assert countries_language_employed_in is None
    else:
        assert Counter(countries_language_employed_in) == Counter(expected_countries)
