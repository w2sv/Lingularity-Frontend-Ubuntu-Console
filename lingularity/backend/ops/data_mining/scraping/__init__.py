from lingularity.backend.utils.module_abstraction import abstractmodulemethod

from . import (
    countries,
    demonym,
    forenames,
    sentence_data_download_links
)


@abstractmodulemethod
def scrape():
    pass
