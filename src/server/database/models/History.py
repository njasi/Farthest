from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class History(Base):
    """
    Stats db table for storing information abt songs that have been played,
    could reasonably have this all in the video table, but im seperatng to avoid
    clutter.


    id:             int, unique id for the model
    skipped:        bool, if this instance was skipped while it was playing
    queue_time:     date, when this video was queued
    start_time:     date, when this video was played
    end_time:       date, when this video finished playing, or when it was skipped
    video_id:       int, foreign key to the videos db; 1:1 mapping
    user_id         int, foregin key to the users db, the user that queued the song
    channel_id      int, the id of the channel this play(ed|ing) in
    """

    __tablename__ = "history"

    id = Column(Integer, primary_key=True)

    time = Column(Integer)
    skipped = Column(Boolean)
    queue_time = Column(Date)
    start_time = Column(Date)
    end_time = Column(Date)

    # Relationships
    # history object should refrence
    #   - one video: duh
    #   - one user: the person who queued it
    #   - one channel: the channel it's playing on
    video = relationship("Video", lazy="joined")
    video_id = Column(Integer, ForeignKey("videos.id"))

    user = relationship("Users", lazy="joined")
    user_id = Column(Integer, ForeignKey("users.id"))

    # dont lazy load cause this is more so its standard with the channel table than
    # actually getting data from there.
    channel = relationship("Channels")
    channel_id = Column(Integer, ForeignKey("channels.id"))

    @staticmethod
    def create(
        video_id: int,
        user_id: int,
        channel_id: int,
        queue_time: Date,
        start_time: Date = None,
        end_time: Date = None,
        skipped: bool = False,
        session=None,
    ):
        """
        Adds a new record to the history db
        """
        if session is None:
            raise ValueError("Session cannot be None")

        history_instance = History(
            video_id=video_id,
            user_id=user_id,
            channel_id=channel_id,
            queue_time=queue_time,
            start_time=start_time,
            end_time=end_time,
            skipped=skipped,
        )

        session.add(history_instance)
        session.commit()
        return history_instance

    @staticmethod
    def update(id, start_time=None, end_time=None, skipped=True, session=None):
        """
        update the given attributes of the history instance with the id

        start_time: when the video starts playing
        end_time:   when the video stops playing (or is skipped)
        skipped:    if the video was skipped
        session:    sqlalchemy session to use
        """
        if session is None:
            raise ValueError("Session cannot be None")

        history_instance = session.query(History).get(id)

        if history_instance is not None:
            if start_time is not None:
                history_instance.start_time = start_time
            if end_time is not None:
                history_instance.end_time = end_time
            history_instance.skipped = skipped

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
