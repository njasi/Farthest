# config the downloaders
import re

from .Downloader import Downloader
from .TestDownloader import TestDownloader
from .YoutubeDownloader import YoutubeDownloader

from .Result import Result
from .exceptions import *

# If you make a new downloader u just need to put it in this list
DOWNLOADERS = [TestDownloader, YoutubeDownloader]
# populated in init
DOWNLOADER_MAP = {}

# TODO make a special thread for downloading / searching

URL_REGEX = r"((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


def list_flags():
    """
    Make a list of the downloader flags
    """
    return [down.site_flag for down in DOWNLOADERS]


def generate_mapping():
    """
    Generate a dict which maps the flags to the downloader classes

        - this is overkill, but meh
    """
    tmp = {}
    for downloader in DOWNLOADERS:
        tmp[downloader.site_flag] = downloader
    return tmp


def lookup_url(url: str):
    """
    Match a url with a downloader usnig ther regexes

    return the matching downloader class
    """
    for downloader in DOWNLOADERS:
        try:
            downloader.assert_site(url)
            return downloader
        except IncorrectDownloaderException:
            pass

    raise NoDownloaderFound


def lookup_flag(flag):
    """
    Return the downloader that matches the given flag
    """
    try:
        return DOWNLOADER_MAP[flag]
    except:
        raise NoDownloaderFound


def search(term, flag="yt", amount=1):
    """
    Search by term, test if its a url as well, and get the details instead
    """
    # check if it's a "url" with basic regex
    if re.match(URL_REGEX, term):
        try:
            downloader = lookup_url(term)
            return downloader.get_details(term)
        except NoDownloaderFound:
            # TODO move on and search it below or error here ?
            pass

    # search by the term usng downloader that matches the flag
    downloader = lookup_flag(flag)
    return downloader.search(term, amount=amount)


def init():
    """
    initalze downloader stuff

    Start up a downloader thread?
    """
    global DOWNLOADER_MAP
    DOWNLOADER_MAP = generate_mapping()

    # not sure abt the best way to handle this
