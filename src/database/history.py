'''
Set of functions to interact with the history database
'''
from database.main import History as HistoryDB
from tinydb.operations import add, increment
from tinydb import Query


class History:
    '''
    Ease of access interface for the History db
    '''
    @staticmethod
    def add_song(id, title, time, user_id):
        '''
        Adds the given song to the history db, incrementing the time played by time,
        if the song is not found a new entry is made

        id:     id of the song (youtube->https://www.youtube.com/watch?v=[id])
        title:  the string title of the song
        time:   the time in seconds that the song played (ie less if skipped or error)
        '''

        # insert or update data
        [did] = HistoryDB.upsert({"id": id, "title": title}, Query().id == id)

        # set initial values if needed
        # this could be much cleaner but I dont feel like it
        HistoryDB.update({"time": 0}, ~Query().time.exists())
        HistoryDB.update({"count": 0}, ~Query().count.exists())

        # update the time and count fields
        HistoryDB.update(add("time", time), doc_ids=[did])
        HistoryDB.update(increment("count"), doc_ids=[did])

# TODO retrieve the history and make viewable through /history, atm just saving the history
