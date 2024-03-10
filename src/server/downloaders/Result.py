TYPE_VIDEO = "TYPE_VIDEO"
TYPE_AUDIO = "TYPE_AUDIO"
TYPE_PLAYLIST = "TYPE_PLAYLIST"
TYPE_LIVESTREAM = "TYPE_LIVESTREAM"


class Result:
    """
    Basically just a struct to hold downloader result information

    - return a list of them in a search
    - a single more populated one when calling get_details
    - one when done downloading

    then we have a single method in the video table where we can update
    the database with one of these


    """

    def __init__(
        self,
        source: str,
        source_id: str,
        url: str,
        title: str = None,
        description: str = None,
        length: int = None,
        resource_url: str = None,
        thumbnail: str = None,
        downloaded: bool = None,
        downloaded_path: str = None,
        type: str = TYPE_VIDEO,
        videos: list["Result"] = None,
    ) -> None:
        # these are needed in all cases
        self.source = source
        self.source_id = source_id
        self.url = url

        # extra details that dont need to be found in initial query
        self.title = title
        self.description = description
        self.length = length
        self.resource_url = resource_url

        # extra stuff that wil only show in webclient
        self.thumbnail = thumbnail

        # for download results
        self.downloaded = downloaded
        self.downloaded_path = downloaded_path

        # for sorting result types, no need for subclasses really
        self.type = type
        # for playlst result
        self.videos = videos

    def __str__(self):
        """
        General case __str__ method cause im tired of memory addrs in debug
        """

        def limit_string(string, amt=25):
            """
            Small helper made to limit the amount of text printed from the descrpton
            """
            if isinstance(type(string), str) and len(string) > amt:
                return string[:amt] + "..."
            return string

        res = f"{type(self).__name__}("
        # add attrs to ignore here
        ignore = ["description"]

        for key in self.__dict__:
            if key not in ignore:
                res += f"\n\t{key} = {limit_string(getattr(self, key))}"
        res += ")\n"
        return res
