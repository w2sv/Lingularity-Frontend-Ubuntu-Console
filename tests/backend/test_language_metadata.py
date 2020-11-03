from lingularity.backend.metadata import language_metadata
from lingularity.backend.ops.data_mining.scraping import sentence_data_download_links


def test_download_link_currency():
    for language, link in sentence_data_download_links.scrape().items():
        assert link == language_metadata[language]['sentenceDataDownloadLinks']['tatoebaProject']
