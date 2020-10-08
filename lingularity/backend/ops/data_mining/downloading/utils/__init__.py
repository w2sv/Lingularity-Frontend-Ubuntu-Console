import urllib as patched_urllib


class AppUrlOpener(patched_urllib.request.FancyURLopener):  # type: ignore
    version = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.69 Safari/537.36'


patched_urllib._urlopener = AppUrlOpener()  # type: ignore
