# make the connection to the tinydb here, import the tables from here
from tinydb import TinyDB
db = TinyDB('data/db.json')

History = db.table('history')
Queue = db.table('queue')
User = db.table('user')

def init():
    """
    Does nothing, but placeholder for if we do need smth
    """