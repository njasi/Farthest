from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base
from streaming.Video import Video


class Queue(Base):
    """
    Queue db table for storing the current queues. Should functonally work like a queue


    id:         int, unique id for the queue item
    history_id  int, fkey to the history table
                (history table includes timing info aand fkeys to user & video)
    """

    __tablename__ = "queue"

    id = Column(Integer, primary_key=True)

    # Relationships
    #   each video owns a stats instance, which is just more details on it
    history = relationship("History")
    history_id = Column(Integer, ForeignKey("history.id"))



class QueueInterace:
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

    def length(self):
        """
        Return the length of the channel's queue
        """
        # TODO

    def is_empty(self):
        """
        Return true if db is empty, false otherwise
        """
        return self.length() == 0

    def enqueue(self, history_id: int, video: Video = None):
        """
        Add the item into the queue, can do with just history id, or
        use an instance of the video class to add (which should have history id in it)
        """
        # TODO

    def dequeue(self):
        """
        Remove the first element of the queue, the one that was currently playing

        for convienence return the new front of the queue
        """
        # TODO

    def get(self, index: int):
        """
        Get the video at the index
        """
        if self.is_empty():
            return None
        # TODO get by idx

    def peek(self):
        """
        Check the first item in the queue, (should be current)
        """
        if self.is_empty():
            return None

        return self.get(0)

    """
    functions below are more related to bot management than queue functionality
    """

    def skip(self, amount: int = 1):
        """
        skip the currently playing song + amount - 1 next songs, None if empty
        """
        # TODO

    def remove(self, idx: int):
        """
        remove the song at index idx from the queue
        """
        # TODO

    def total_time(self):
        """
        Calculate the current length of the queue,
        excluding the currently playing song
        """
        # TODO
        # get all except 0 and return a sum


from streaming.Video import Video
