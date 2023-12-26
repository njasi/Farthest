'''
Set of functions to interact with the history database
'''
from database.main import User as UserDB
from tinydb.operations import add, increment
from tinydb import Query


class Users:
    '''
    Ease of access interface for the User db
    '''

    @staticmethod
    def ensure_exists(self, user_id):
        # insert or update data
        did = UserDB.get({"id": user_id})
        if did is None:
            did = UserDB.insert({
                "id": user_id,
                "time": 0,
                "count": 0,
                "skips": 0,
            })
        return did

    @staticmethod
    def add_play(self, time, user_id):
        '''
        Saves data on how many songs a user queued, and for how long

        time:       the time in seconds that the song played (ie less if skipped or error)
        user_id:    the telegram user id of the user who queued the song
        '''
        did = self.ensure_exists(user_id)

        # update the time and count fields
        UserDB.update(add("time", time), doc_ids=[did])
        UserDB.update(increment("count"), doc_ids=[did])

    @staticmethod
    def add_skip(self, user_id):
        '''
        Add a song skip to the users history

        user_id:    the telegram user id of the user who skipped the song
        '''

        did = self.ensure_exists(user_id)

        # update the skip field
        UserDB.update(increment("skips"), doc_ids=[did])
