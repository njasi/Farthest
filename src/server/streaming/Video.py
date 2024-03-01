from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from downloaders import Downloader
# the above block is just for type hinting. DOing this
# allows us to avoid circular import

import vlc
import time
import datetime


class NoDownloader(Exception):
    pass


class Video:
    def __init__(
        self,
        url: str,
        title: str = "",
        length=-1,
        downloader: Downloader = None,
        user_id=None,
    ):
        # the downloader related to this video
        self.downloader = downloader

        # resource info
        self.url = url
        self.resource_url
        # none if not downloaded, path otherwise
        self.resource_path = None

        # actual content info
        self.audio_only = False
        self.length = length
        self.time = -1

        # details
        self.title = title
        self.user_id = user_id

    @staticmethod
    def from_Queue_item(item):
        newVid = Video(
            url=item["url"],
            title=item["title"],
            length=item["length"],
            user_id=item["user_id"],
        )

        newVid.resource_url = item["resource_url"]
        newVid.resource_path = item["resource_path"]

        return newVid

    def get_id(self):
        self.downloader.get_id(self.url)

    def assert_downloader(self) -> None:
        """
        assert that this video has a paired downloader
        raises NoDownloader error otherwise
        """
        if self.downloader is None:
            raise NoDownloader()

    def download(self):
        """
        Download the content to disk, returns the path.
        if it already exists dont download, just give resource
        """

        self.assert_downloader()

        # check if downloaded, return filepath if so
        path = self.downloader.is_downloaded(self.url)
        if path is not None:
            self.resource_path = path
            return path

        # otherwise download it, save url for use incase vid plays before download
        self.resource_url = self.downloader.get_resource()
        # TODO maybe start the download in its own thread,
        # TODO how to interact with messages? ie update /q response to "downloading..." to "queued" idk
        # could pass a callback to download with the info needed to edit the message
        self.downloader.download()

    def get_resource(self):
        """
        get the resource url
        """
        if not self.resource_url or self.resource_path:
            self.assert_downloader()
            self.resource_url = self.downloader.get_resource(self.url)
            return self.resource_url

        # already have it, or its downloaded
        return self.resource_url or self.resource_path

    def __str__(self):
        result = ""

        if self.time == -1:
            result = f"({datetime.timedelta(seconds=self.length)})"
        else:
            result = f"({datetime.timedelta(seconds=int(self.time))}/{datetime.timedelta(seconds=self.length)})"

        result = f"<b><a href={self.url}>{self.title}</a></b> - ({result})"

        return result
