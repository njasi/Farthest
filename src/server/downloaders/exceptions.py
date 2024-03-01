class NoDownloaderFound(Exception):
    """
    Raise when a method cannot find a downloader,
        - can't find by flag (no downloader with flag)
        - url doesn't match any downloader regex
    """

    def __init__(self, msg="Could not find a matching downloader", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class IncorrectDownloaderException(Exception):
    pass


class UnexpectedFileExtension(Exception):
    pass
