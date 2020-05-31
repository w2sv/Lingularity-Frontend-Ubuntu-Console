from src.webpage_interaction import ContentRetriever


def test_zip_download_link_parsing():
    content_retriever = ContentRetriever()
    content_retriever.get_language_ziplink_dict()
    if content_retriever.languages_2_ziplinks is not None:
        assert all(k.endswith('.zip') for k in content_retriever.languages_2_ziplinks.values())

        # check if number of languages has changed
        if (n_languages := len(content_retriever.languages_2_ziplinks)) != 79:
            print(f'# of available languages has changed: {n_languages}')
