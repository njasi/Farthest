# config the downloaders
from .Downloader import Downloader
from .TestDownloader import TestDownloader
from .exceptions import *

DOWNLOADERS = [TestDownloader]

# TODO make a special thread for downloading / searching

def lookup(flag):
    for downloader in DOWNLOADERS:
        if flag == downloader.site_flag:
            return downloader

    raise NoDownloaderFound


def search(term, flag="test"):
    """
    search with the matching downloader
    """
    downloader = lookup(flag)
    return downloader.search(term)

