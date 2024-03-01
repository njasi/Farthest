import re

from downloaders.Downloader import Downloader
from streaming.Video import Video


class TestDownloader(Downloader):
    # regex to check if url is from the site
    site_regex = re.compile("test")
    # the flag to use if you want to use this downloader
    site_flag = "test"
    # pretty name to use in messages
    site_name = "Test Downloader"
    # the expected file extension on resources this would download
    expected_resource_types = ["mp4"]

    @classmethod
    def search(cls, term: str) -> list[Video]:
        """
        Search for a video, returns list of search results
        """

        test_vid = Video(
            "./downloaded/test.mp4",
            title="Test Video",
            length=1000,
            downloader=cls,
            user_id=0,
        )
        test_vid.resource_path = "./downloaded/test.mp4"
        return [test_vid]

    @staticmethod
    def get_resource(url: str, video: Video = None) -> str:
        """
        get the actual resource for the video / audio that can be downloaded or streamed
        """
        if video is not None:
            url = video.url
        

        return url

    @staticmethod
    def get_details(url: str):
        """
        get details about the resource at the url, title etc
        """

        print("Get details")
