from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database.base import Base



class Video(Base):
    """
    Video db table for storing information abt songs that have been played


    id:                 int, unique id for the model
    title:              str, the title of the song
    description:        str, any description given to the video
    source:             str, the flag of the site that it originated from
    source_id:          str, the uid that the source uses: youtube->https://www.youtube.com/watch?v=[id]
    url                 str, the url for the video
    resource_url        str, the url of the video resource itself
    downloaded:         bool, if the video has been downloaded
    downloaded_path     str, the path of the downloaded resource
    """

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)

    # basic details of the video
    title = Column(String)
    description = Column(String)

    # original source info
    source = Column(String(8)) # the source flag shld be small so
    source_id = Column(String)
    url = Column(String)
    resource_url = Column(String)

    # internal info
    downloaded = Column(Boolean)
    downloaded_path = Column(String) # should be derivable but just in case


    # Relationships
    #   each video owns a stats instance, which is just more details on it
    stats = relationship("Stats")

    def __init__(self, title, release_date):
        self.title = title
        self.release_date = release_date

    @staticmethod
    def find_or_create(
        source: str, source_id: str, title: str = "", id: int = None, session=None
    ):
        """
        Adds the video to the video db, and returns it
        - if the song is not found a new entry is made
        - source_id + source should be unique, how to check if the song has been played before

        source:     the flag of the site its from ("yt", "test", etc)
        source_id:  id of the song (youtube->https://www.youtube.com/watch?v=[id])
        title:      the string title of the song
        """
        # TODO find / create model then fill wth the option nal attribubtes
