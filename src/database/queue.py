'''
Set of functions used to interact with the queue database
'''
from datetime import now
from database.main import Queue as QueueDB
from tinydb.operations import decrement


class Queue:
    '''
    This isnt a proper queue class, just a convienent wrapper for the Queue db

    Actual timing will be handled in the audio queue
    '''

    @staticmethod
    def is_empty():
        '''
        Return true if db is empty, false otherwise
        '''
        return len(QueueDB) == 0

    @staticmethod
    def add(id, title, length, url, user_id):
        '''
        add the song into the queue
        '''
        entry = {"id": id,
                 "title": title,
                 "length": length,
                 "url": url,
                 "user_id": user_id,
                 "created_at": now(),
                 "position": len(QueueDB)}
        if Queue.is_empty():
            entry["current"] = True
        QueueDB.insert(entry)

    @staticmethod
    def pop():
        '''
        Pop off the top song, ie currently playing

        Nonstandard, but for convienence: return the new front of the queue
        '''
        res = None

        if Queue.is_empty():
            return res

        # grab the song with position 0 (currently playing)
        QueueDB.remove({"position": 0})
        if not Queue.is_empty():
            # lower the position of all entries
            QueueDB.update(decrement("position"))
            # grab the new front of the queue
            res = QueueDB.get({"position": 0})

        return res

    @staticmethod
    def get(index):
        '''
        Get the song at the index
        '''
        if Queue.is_empty():
            return None
        return QueueDB.get({"position": index})

    @staticmethod
    def next():
        '''
        get the next song in the queue, None if empty
        '''
        return Queue.get(self, 1)

    @staticmethod
    def skip(amount=1):
        '''
        skip the currently playing song + amount - 1 next songs, None if empty
        '''
        pass

    @staticmethod
    def current():
        '''
        get the currently playing song, None if empty
        '''
        if Queue.is_empty():
            return None

        return Queue.get(0)

    @staticmethod
    def remove(idx: int):
        '''
        remove the song at index idx from the queue
        '''
        pass

    @staticmethod
    def total_time() -> int:
        '''
        Calculate the current length of the queue,
        excluding the currently playing song
        '''
        songs = QueueDB.search(QueueDB.position > 0)
        return sum([song.length for song in songs])

    @staticmethod
    def to_message(page=0) -> str:
        '''
        turn the queue into a message representation
        '''
