from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from .base import Base
from database.models.Stats import Stats


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
    source = Column(String(8))  # the source flag shld be small so
    source_id = Column(String)
    url = Column(String)
    resource_url = Column(String)

    # internal info
    downloaded = Column(Boolean, default=False)
    downloaded_path = Column(String)  # should be derivable but just in case

    # Relationships
    #   each video owns a stats instance, which is just more details on it
    stats = relationship("Stats")

    def __init__(self, title, release_date):
        self.title = title
        self.release_date = release_date

    @staticmethod
    def find_or_create(
        source: str,
        source_id: str,
        title: str = None,
        description: str = None,
        url: str = None,
        resource_url: str = None,
        session=None,
    ):
        """
        Adds the video to the video db, and returns it
        - if the song is not found a new entry is made
        - source_id + source should be unique, how to check if the song has been played before
        - if creating the new entry make a related stats entry as well

        source:         the flag of the site its from ("yt", "test", etc)
        source_id:      id of the song (youtube->https://www.youtube.com/watch?v=[id])
        title:          the string title of the video
        description:    the descripton of the video, for something like yt its the literal description section
        url:            the url to the page that has the video
        resource_url    url to the actual video file
        session:        sqlalchemy session to use
        """

        if session is None:
            raise ValueError("Session cannot be None")

        video = None

        try:
            # Try to find an existing video by source and source_id
            # together they should be unique
            video = (
                session.query(Video).filter_by(source=source, source_id=source_id).one()
            )

        except NoResultFound:
            # If not found, create a new entry
            video = Video(
                source=source,
                source_id=source_id,
                title=title,
                description=description,
                url=url,
                resource_url=resource_url,
            )
            # add the video, then add stats & commit
            session.add(video)

            # Create a related stats entry
            stats = Stats(video_id=video.id)
            session.add(stats)
            session.commit()

        return video
