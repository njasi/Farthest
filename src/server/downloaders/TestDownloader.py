import re

from downloaders.Downloader import Downloader
from .Result import Result


class TestDownloader(Downloader):
    # regex to check if url is from the site
    site_regex = re.compile("(?!x)x")  # this wont match anything
    # the flag to use if you want to use this downloader
    site_flag = "test"
    # pretty name to use in messages
    site_name = "Testsource"
    # the expected file extension on resources this would download
    expected_resource_types = ["mp4"]

    @classmethod
    def search(cls, term: str) -> list[Result]:
        """
        Search for a video, returns list of search results
        """

        test_video = Result(
            source=cls.site_flag,
            source_id="test_id",
            url=None,
            title="Test video title",
            downloaded_path="./downloaded/test.mp4",
            downloaded=True,
        )
        return [test_video]

    @staticmethod
    def get_resource(url: str, video: Result = None) -> str:
        """
        get the actual resource for the video / audio that can be downloaded or streamed
        """
        if video is not None:
            url = video.url

        return url

    @staticmethod
    def get_details(url: str) -> Result:
        """
        get details about the resource at the url that may not have come with the
        search function
        """

        return Result(
            source="test",
            source_id="test_id",
            url=url,
            title="Test video title",
            descrption="this is the description of a est video",
            length=635,
            downloaded=True,
            downloaded_path="./downloaded/test.mp4",
        )
