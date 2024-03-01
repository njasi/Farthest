"""
Set of functions to interact with the history database
"""

from tinydb.operations import add, increment
from tinydb import Query
from . import User as UserDB

# i despise how tinydb handles queries
# just lemme pass a dict
User = Query()

class Users:
    """
    Ease of access interface for the User db
    """

    @staticmethod
    def ensure_exists(user_id):
        # insert or update data
        # id is telegram id
        did = UserDB.get(User.id == user_id)
        if did is None:
            did = UserDB.insert(
                {
                    "id": user_id,
                    "time": 0,
                    "count": 0,
                    "skips": 0,
                }
            )
        else:
            did = did.doc_id
        return did

    @staticmethod
    def add_play(time, user_id):
        """
        Saves data on how many songs a user queued, and for how long

        time:       the time in seconds that the song played (ie less if skipped or error)
        user_id:    the telegram user id of the user who queued the song
        """
        did = Users.ensure_exists(user_id)

        # update the time and count fields
        print(time, did)
        UserDB.update(add("time", time), doc_ids=[did])
        UserDB.update(increment("count"), doc_ids=[did])

    @staticmethod
    def add_skip(user_id):
        """
        Add a song skip to the users history

        user_id:    the telegram user id of the user who skipped the song
        """

        did = Users.ensure_exists(user_id)

        # update the skip field
        UserDB.update(increment("skips"), doc_ids=[did])
