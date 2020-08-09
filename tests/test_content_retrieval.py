from lingularity.backend.sentence_data_fetcher import SentenceDataFetcher


def test_zip_download_link_parsing():
    content_retriever = SentenceDataFetcher()
    content_retriever.get_language_ziplink_dict()
    if content_retriever.language_2_ziplink is not None:
        assert all(k.endswith('.zip') for k in content_retriever.language_2_ziplink.values())

        # check if number of languages has changed
        if (n_languages := len(content_retriever.language_2_ziplink)) != 79:
            print(f'# of available languages has changed: {n_languages}')
