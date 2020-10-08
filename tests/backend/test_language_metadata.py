from lingularity.backend.metadata import language_metadata
from lingularity.backend.ops.data_mining.scraping import scrape_sentence_data_download_links


def test_metadata_actuality():
    for language, link in scrape_sentence_data_download_links().items():
        assert language == language_metadata[language]['sentenceDataDownloadLink']['tatoebaProject']
