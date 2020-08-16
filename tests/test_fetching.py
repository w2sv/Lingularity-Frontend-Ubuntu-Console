import pytest
from itertools import chain
from collections import Counter

from lingularity.backend.data_fetching.scraping.sentence_data import SentenceDataFetcher
from lingularity.backend.data_fetching.scraping.demonyms import scrape_demonyms
from lingularity.backend.data_fetching.scraping.language_typical_forenames import _scrape_countries_language_employed_in, _scrape_popular_forenames


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
    ('Indogermanic', None)
])
def test_demonyms_fetching(country, expected_demonyms):
    assert scrape_demonyms(country) == expected_demonyms


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
        assert Counter(_scrape_countries_language_employed_in(language)) == Counter(expected_countries)
    else:
        assert _scrape_countries_language_employed_in(language) == expected_countries


@pytest.mark.parametrize('country,expected_forenames', [
    ('France', [['Gabriel', 'Louis', 'Raphaël', 'Jules', 'Adam', 'Lucas', 'Léo', 'Hugo', 'Arthur', 'Nathan'], ['Emma', 'Louise', 'Jade', 'Alice', 'Chloé', 'Lina', 'Mila', 'Léa', 'Manon', 'Rose']]),
    ('Germany', [['Ben', 'Jonas', 'Leon', 'Elias', 'Finn', 'Noah', 'Paul', 'Luis', 'Lukas', 'Luca'], ['Mia', 'Emma', 'Hannah', 'Sofia', 'Anna', 'Emilia', 'Lina', 'Marie', 'Lena', 'Mila']]),
    ('Spain', [['Hugo', 'Daniel', 'Martín', 'Pablo', 'Alejandro', 'Lucas', 'Álvaro', 'Adrián', 'Mateo', 'David'], ['Markel', 'Aimar', 'Jon', 'Ibai', 'Julen', 'Ander', 'Unax', 'Oier', 'Mikel', 'Iker']]),
    ('Korea', [['Min-jun', 'Seo-jun', 'Joo-won', 'Ye-jun', 'Shi-woo', 'Jun-seo', 'Do-yoon (도윤)', 'Hyun-woo', 'Gun-woo', 'Ji-hoon'], ['Seo-yeon', 'Seo-yun', 'Ji-woo', 'Seo-hyeon', 'Min-seo', 'Yun-o', 'Chae-won', 'Ha-yoon', 'Ji-ah (지아)', 'Eun-seo']]),
    ('Japan', [['Sō', 'Itsuki', 'Ren', 'Hinata', 'Asahi', 'Sōta', 'Yuuma', 'Arata', 'Ryō', 'Yūto'], ['Sakura', 'Riko', 'Aoi', 'Wakana', 'Sakura', 'Rin', 'Anna', 'Himari', 'Yuna', 'Kaed']])
])
def test_forename_scraping(country, expected_forenames):
    get_flattened_set = lambda forenames_list: set(chain.from_iterable(forenames_list))
    assert not len(get_flattened_set(_scrape_popular_forenames(country)) ^ get_flattened_set(expected_forenames))
