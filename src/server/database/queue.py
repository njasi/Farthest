"""
Set of functions used to interact with the queue database
"""
import time
from tinydb.operations import decrement, subtract
from tinydb import where

from . import Queue as QueueDB
from streaming.Video import Video

# TODO might need to make these operations thread safe


class Queue:
    """
    This isnt a proper queue class, just a convienent wrapper for the Queue db

    Simply to keep track of what is playing

    Actual timing will be handled in the audio queue

    Current video should always be 0, unless u r between an operation
    """

    def __init__(self, channel):
        self.channel = channel

    def is_empty(self):
        """
        Return true if db is empty, false otherwise
        """
        return self.length() == 0

    def update_current(self):
        QueueDB.update(
            {"current": True}, where("channel") == self.channel & where("position") == 0
        )

    def length(self):
        return QueueDB.count(where("channel") == self.channel)

    def add(self, id, title, length, url, user_id, source="yt"):
        """
        add the song into the queue
        """
        entry = {
            # resource info
            "url": url,
            "resource_url": None,
            "resource_path": None,
            # actual content info
            "length": length,
            # details
            "title": title,
            "user_id": user_id,
            # queueDB specific
            "id": id,
            "source": source,  # could map to downloader
            "current": False,
            "position": self.length(),
            "channel": self.channel,
            "created_at": int(time.time()),
        }
        if self.is_empty():
            entry["current"] = True
        QueueDB.insert(entry)
        return entry

    def pop(self):
        """
        Pop off the top song, ie currently playing

        Nonstandard, but for convienence: return the new front of the queue
        """
        res = None

        if self.is_empty():
            return res

        # grab the song with position 0 (currently playing)
        QueueDB.remove({"position": 0, "channel": self.channel})
        if not self.is_empty():
            # lower the position of all entries
            QueueDB.update(decrement("position"), where("channel") == self.channel)
            # grab the new front of the queue
            res = QueueDB.get({"position": 0}, where("channel") == self.channel)
            self.update_current()

        return res

    def get(self, index):
        """
        Get the song at the index
        """
        if self.is_empty():
            return None
        return QueueDB.get({"position": index, "channel": self.channel})

    def next(self):
        """
        get the next song in the queue, None if empty
        """
        # TODO what happened here
        first = Queue.get({"position": 0, "channel": self.channel})
        if first.current is not None:
            return Queue.get({"position": 1, "channel": self.channel})
        else:
            return first

    def skip(self, amount=1):
        """
        skip the currently playing song + amount - 1 next songs, None if empty
        """

        QueueDB.update(subtract("position", amount), where("channel") == self.channel)
        QueueDB.remove(where("position") < 0)
        newCurrent = QueueDB.get(where("position") == 0)
        self.update_current()

        if newCurrent:
            return newCurrent

        # TODO: perhaps an error raise here instead
        return None

    def current(self):
        """
        get the currently playing song, None if empty
        """
        if self.is_empty():
            return None

        return Queue.get(0)

    def remove(self, idx: int):
        """
        remove the song at index idx from the queue
        """
        QueueDB.remove({"position": idx, "channel": self.channel})
        # shift the upper ones now
        QueueDB.update(
            decrement(), where("position") > idx & where("channel") == self.channel_id
        )
        # set the pos 0 item to the current
        self.update_current()

    def total_time(self) -> int:
        """
        Calculate the current length of the queue,
        excluding the currently playing song
        """
        songs = QueueDB.search(QueueDB.position > 0 & where("channel") == self.channel)
        return sum([song.length for song in songs])

    # def update_details(self, Video):
    #     """
    #     add details from the Video instance witch represents this in the queue array
    #     """
