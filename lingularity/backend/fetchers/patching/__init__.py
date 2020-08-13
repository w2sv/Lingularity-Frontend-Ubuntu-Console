import urllib.request


class AppUrlOpener(urllib.request.FancyURLopener):
    version = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.69 Safari/537.36'


urllib._urlopener = AppUrlOpener()  # type: ignore

patched_urllib = urllib