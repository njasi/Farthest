import re
import yt_dlp
import json

from .exceptions import *
from .Result import Result, TYPE_PLAYLIST, TYPE_LIVESTREAM
from .Downloader import Downloader


ydl_opts = {
    "match_filter": yt_dlp.utils.match_filter_func("!is_live"),
    "format": "mp4",
    "noplaylist": True,
    "silent": True,
}


# an informal interface we are gonna use for standardization
class YoutubeDownloader(Downloader):
    # regex to check if url is from the site
    site_regex = re.compile(
        "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)(?P<id>[\w\-]+)(\S+)?$"
    )
    # the flag to use if you want to use this downloader
    site_flag = "yt"
    site_name = "Youtube"
    # the expected file extension on resources this would download
    # ive made ytdl choose mp4 type vids to make it simple
    expected_resource_types = ["mp4"]

    @classmethod
    def parse_entry_to_result(cls, entry) -> "Result":
        """
        Parse the annoying entry json into a result list
        (list only to deal with playlists)
        """

        with open("test_live.json", "w+") as file:
            file.write(json.dumps(entry))

        base = Result(
            source="yt",
            source_id=entry["id"],
            url=entry["original_url"],
            title=entry["title"],
            description=entry["description"],
        )

        if "is_live" in entry and entry["is_live"]:
            # check if its a livestream
            base.type = TYPE_LIVESTREAM
            base.thumbnail = entry["thumbnail"]
            # TODO pick a format as the resource_url if we ever want to
            # play livestreams
        elif "_type" in entry and entry["_type"] == "playlist":
            # check if playlist and parse all the vids in it
            base.type = TYPE_PLAYLIST
            base.videos = []
            for e in entry["entries"]:
                base.videos += [cls.parse_entry_to_result(e)]
        else:
            # normal videos have these
            base.thumbnail = entry["thumbnail"]
            base.length = entry["duration"]
            base.resource_url = entry["url"]

        return base

    @classmethod
    def search(cls, term: str, amount: int = 1) -> list["Result"]:
        """
        Search for a video, returns list of search results
        """

        results = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"ytsearch{amount}:{term}", download=False)

            for entry in res["entries"]:
                results += [cls.parse_entry_to_result(entry)]

        return results

    @classmethod
    def get_resource(cls, url: str) -> str:
        """
        get the actual resource for the video / audio that can be downloaded or streamed
        """

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url=url, download=False)
            result = cls.parse_entry_to_result(res)
            if result.type == TYPE_PLAYLIST:
                return None
            return result.url

    @classmethod
    def get_details(cls, url: str) -> "Result":
        """
        get details about the resource at the url, title etc

        - might need to use to get information lke video length
        - may also return the resource url
        """

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url=url, download=False)

            with open("test_paylist.json", "w") as file:
                file.write(json.dumps(res))

            result = cls.parse_entry_to_result(res)
            return result


if __name__ == "__main__":
    # test the stuff

    # do a simple search
    print(YoutubeDownloader.search("amogus drip", amount=1)[0])

    # get details of a single video by url
    print(YoutubeDownloader.get_details("https://www.youtube.com/watch?v=laZusNy8QiY"))

    # get details of a livestream

    # get details of a playlist
    print(
        YoutubeDownloader.get_details(
            "https://www.youtube.com/playlist?list=PL3817D41C7D841E23"
        )
    )
