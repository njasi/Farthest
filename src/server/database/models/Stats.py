from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base



class Stats(Base):
    """
    Stats db table for storing information abt songs that have been played,
    could reasonably have this all in the video table, but im seperatng to avoid
    clutter.


    id:         int, unique id for the model
    video_id    int, foreign key to the videos db; 1:1 mapping
    time:       int, the total time in seconds that this song has played for
    skips:      int, how many times it has been skipped
    play_count: int, times the song has been queued
    last_play:  date, the most recent time that it was played
    """

    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)

    time = Column(Integer)
    skips = Column(Integer)
    play_count = Column(Integer)
    last_play = Column(Date)

    # Relationships
    # a stats instance is related to one video ofc
    stats = relationship("Videos")
    video_id = Column(Integer, ForeignKey("videos.id"))

    def __init__(self, title, release_date):
        self.title = title
        self.release_date = release_date

    @staticmethod
    def add_data(
        video_id: int, title: str, time: int, skipped: bool = False, session=None
    ):
        """
        Adds the given song to the history db, incrementing the time played by time &
        adding a skip to the count if skipped is true
        - if the song is not found a new entry is made
        - sets last_play to current time
        - source_id + source should be unique, this is how we find the song

        video_id:   the fkey to the video
        title:      the string title of the song
        time:       the time in seconds that the song played (ie less if skipped or error)
        skipped:    if the song was skipped, false if played all the way through
        session:    sql alchemy session to use if specified
        """
        # TODO


#     @staticmethod
#     def add_song(id, title, time, user_id, source="yt"):
#         """
#         Adds the given song to the history db, incrementing the time played by time,
#         if the song is not found a new entry is made

#         id:     id of the song (youtube->https://www.youtube.com/watch?v=[id])
#         title:  the string title of the song
#         time:   the time in seconds that the song played (ie less if skipped or error)
#         source: the flag of the site its from
#         """

#         # insert or update data
#         [did] = HistoryDB.upsert(
#             {"id": id, "title": title, "source": source}, Query().id == id
#         )

#         # set initial values if needed
#         # this could be much cleaner but I dont feel like it
#         HistoryDB.update({"time": 0}, ~Query().time.exists())
#         HistoryDB.update({"count": 0}, ~Query().count.exists())

#         # update the time and count fields
#         HistoryDB.update(add("time", time), doc_ids=[did])
#         HistoryDB.update(increment("count"), doc_ids=[did])

# # TODO retrieve the history and make viewable through /history, atm just saving the history

