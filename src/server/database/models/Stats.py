import datetime

from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


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

    time = Column(Integer, default=0)
    skips = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    last_play = Column(Date, default=None)

    # Relationships
    # a stats instance is related to one video ofc
    video = relationship("Video", back_populates="stats", uselist=False)
    video_id = Column(Integer, ForeignKey("videos.id"))

    @staticmethod
    def add_data(video_id: int, time: int, skipped: bool = False, session=None):
        """
        Updaates data in the stats instance, incrementing the time played by time,
        adding a skip to the count if skipped is true, and adding to playcount
        - if the song is not found a new entry is made
        - sets last_play to current time

        video_id:   the fkey to the video
        time:       the time in seconds that the song played (ie less if skipped or error)
        skipped:    if the song was skipped, false if played all the way through
        session:    sql alchemy session to use if specified
        """

        if session is None:
            raise ValueError("Session cannot be None")

        stats_entry = session.query(Stats).filter_by(video_id=video_id).first()

        if stats_entry is None:
            return
            # TODO probably raise an error here instead

        # Update the stats entry
        stats_entry.time += time
        stats_entry.play_count += 1

        if skipped:
            stats_entry.skips += 1

        stats_entry.last_play = datetime.now()

        session.commit()

    def __str__(self):
        """
        General case __str__ method cause im tired of memory addrs in debug
        """
        res = f"{type(self).__name__}("
        # add attrs to ignore here
        ignore = []

        columns = [m.key for m in self.__table__.columns]

        for key in columns:
            if key not in ignore:
                res += f"\n\t{key} = {getattr(self, key)}"
        res += ")\n"
        return res
