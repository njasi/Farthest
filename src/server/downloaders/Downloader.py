import re
import os
from urllib.parse import urlparse
from urllib.request import urlretrieve

from streaming.Video import Video
from .exceptions import *

# TODO: make url based functions also work for videos as arguments,

# an informal interface we are gonna use for standardization
class Downloader:
    # regex to check if url is from the site
    site_regex = re.compile("")
    # the flag to use if you want to use this downloader
    site_flag = None
    # the expected file extension on resources this would download
    expected_resource_types = ["mp4"]

    @staticmethod
    def search(term: str) -> list[Video]:
        """
        Search for a video, returns list of search results
        """

        # TODO implement on per class basis
        return []

    @staticmethod
    def get_resource(url: str) -> str:
        """
        get the actual resource for the video / audio that can be downloaded or streamed
        """

        # TODO implement on per class basis
        pass

    @staticmethod
    def get_details(url: str):
        """
        get details about the resource at the url, title etc
        """

        # TODO implement on per class basis
        pass


    @classmethod
    def assert_site(cls, url: str) -> bool:
        """
        Assert that the url matches the site, raise error if not
        """
        if re.match(cls.site_regex, url):
            return True
        raise IncorrectDownloaderException()

    @classmethod
    def get_id(cls, url):
        """
        get unique id for the resource, default id is:
            site_flag + base + hostname
        """
        resource_info = urlparse(url)

        base, ext = os.path.splitext(os.path.basename(resource_info.path))

        # give unique id
        return f"{cls.site_flag}_{base}_{resource_info.hostname}"

    @classmethod
    def get_resource_path(cls, url: str, resource_url: str) -> str:
        """
        Check the resource url and make a path from this
        """
        # generate the id based off of url
        id = cls.get_id(url)
        # grab the extension, assert it is expected
        resource_info = urlparse.urlparse(resource_url)

        _, ext = os.path.splitext(os.path.basename(resource_info.path))
        if not ext in cls.expected_resource_types:
            raise UnexpectedFileExtension()

        # give unique name & download
        file_path = f"{id}.{ext}"
        urlretrieve(resource_url, filename=file_path)

    @classmethod
    def download(cls, url: str):
        """
        Download the given url, assert is from the same site
        """
        cls.assert_site(url)
        resource_url = cls.get_resource(url)

        cls.get_resource_path(resource_url)
