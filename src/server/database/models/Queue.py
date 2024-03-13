import datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, update, func
from sqlalchemy.orm import relationship, contains_eager

from .base import Base
from .History import History

TITLE_LENGTH_LIMIT = 40


class Queue(Base):
    """
    Queue db table for storing the current queues. Should functonally work like a queue


    id:         int, unique id for the queue item
    history_id  int, fkey to the history table
                (history table includes timing info aand fkeys to user & video)
    position    int, the position in the queue
    """

    __tablename__ = "queue"

    id = Column(Integer, primary_key=True)
    position = Column(Integer)

    # Relationships
    #   each queue object is literally just a history obj with a position
    #   in the queue
    history = relationship("History", lazy="joined")
    history_id = Column(Integer, ForeignKey("history.id"))

    channel = relationship("Channels")
    channel_id = Column(Integer, ForeignKey("channels.id"))

    def telegram_str(self):
        """
        Basically to string method, but meant to be used in a list in telegram

        html formatted string™
        """

        # chop up the title so we dont have multi line messes
        title = self.history.video.title
        title = (
            (title[:TITLE_LENGTH_LIMIT] + "...")
            if len(title) > TITLE_LENGTH_LIMIT
            else title
        )

        return (
            f"[{self.position + 1}]"
            f"\t<a href='{self.history.video.url}'>{title}</a>"
            f"\t({datetime.timedelta(seconds=self.history.video.length)})"
        )

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


class QueueInterface:
    """
    Class to interface with the queue db in a more "queuelike" manner

    -   Simply to keep track of what is playing
    -   Actual timing will be handled in the audio queue
    -   Current video should always be 0, unless u r between an operation
    """

    def __init__(self, channel):
        """
        channel: the id of the channel that this queue is managing, since the db has multiple queues in it
        """
        self.channel = channel

    def length(self, session=None):
        """
        Return the length of the channel's queue
        """
        return session.query(Queue).filter_by(channel_id=self.channel).count()

    def is_empty(self, session=None):
        """
        Return true if db is empty, false otherwise
        """
        return self.length(session) == 0

    def enqueue(self, history_id: int, video=None, session=None):
        """
        Add the item into the queue, can do with just history id, or
        use an instance of the video class to add (which should have history id in it)
        """

        if video is not None:
            history_id = video.history_id

        if session is None:
            raise ValueError("Session cannot be None")

        # query for the position number
        last_position = (
            session.query(func.max(Queue.position))
            .filter_by(channel_id=self.channel)
            .scalar()
        )
        position = 0 if last_position is None else last_position + 1

        queue_item = Queue(
            history_id=history_id, position=position, channel_id=self.channel
        )
        session.add(queue_item)
        session.commit()

        # TODO maybe return the position picked so that we can tell if it was the new first element

    def dequeue(self, session=None):
        """
        Remove the first element of the queue, the one that was currently playing

        for convienence return the new front of the queue
        """
        if session is None:
            raise ValueError("Session cannot be None")

        front_item = (
            session.query(Queue).filter_by(channel_id=self.channel, position=0).first()
        )

        if front_item:
            session.delete(front_item)

            # Update positions of remaining items in the queue
            session.execute(
                update(Queue)
                .filter_by(channel_id=self.channel)
                .values(position=Queue.position - 1)
            )
            session.commit()

        return self.peek()

    def get(self, index: int, session=None):
        """
        Get the video at the index
        """
        if self.is_empty():
            return None

        if session is None:
            raise ValueError("Session cannot be None")

        queue_item = (
            session.query(Queue)
            .filter_by(channel_id=self.channel, position=index)
            .first()
        )

        return queue_item

    def peek(self, session=None):
        """
        Check the first item in the queue, (should be current)
        """
        if self.is_empty():
            return None

        return self.get(0, session)

    """
    functions below are more related to bot management than queue functionality
    """

    def skip(self, amount: int = 1, session=None):
        """
        skip the currently playing song + amount - 1 next songs, None if empty
        """
        if session is None:
            raise ValueError("Session cannot be None")

        skipped = [self.peek(session=session)]
        for _ in range(amount):
            skipped += [self.dequeue(session)]

        # do all but the last, cause of dequque returning the new front
        return skipped[:-1]

    def remove(self, idx: int, session=None):
        """
        remove the song at index idx from the queue
        """
        if self.is_empty():
            return None

        if session is None:
            raise ValueError("Session cannot be None")

        # get the one to remove
        queue_item = (
            session.query(Queue)
            .filter_by(channel_id=self.channel, position=idx)
            .first()
        )

        if queue_item:
            # delete it duh
            session.delete(queue_item)

            # update the positons of the ones after it
            session.execute(
                update(Queue)
                .filter_by(channel_id=self.channel)
                .values(position=Queue.position > idx)
            )

            session.commit()

            return queue_item
        return None

    def get_range(self, idx: int = 0, amount: int = 0, session=None):
        """
        Get the queue elements with a position >=idx
        and <idx + amount

        idx:        int, the index to start at
        amount:     int, the amount of elements to get after idx
        session:    the sqlalchemy session to use
        """
        if amount <= 0:
            return []

        queue_elements = (
            session.query(Queue)
            .filter(Queue.position >= idx)
            .filter(Queue.position < idx + amount)
            .order_by(Queue.position)
            .all()
        )

        return queue_elements

    def total_time(self, session=None):
        """
        Calculate the current length of the queue,
        excluding the currently playing song
        """

        if session is None:
            raise ValueError("Session cannot be None")

        # get all except 0 and return a sum
        result = (
            session.query(Queue)
            .filter(Queue.channel_id == self.channel)
            .filter(Queue.position > 0)
        )

        return sum(item.history.video.length for item in result) if result else 0
