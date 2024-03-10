import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# import all the models
from .models.Queue import Queue, QueueInterface
from .models.Stats import Stats
from .models.Users import Users
from .models.Video import Video
from .models.History import History
from .models.Channels import Channels

from .models.base import metadata

# basic URI config
db_name = os.environ.get("DATABASE_NAME", "farther")
db_user = os.environ.get("DATABASE_USER", "nick")
db_pass = os.environ.get("DATABASE_PASS", "password")
db_host = os.environ.get("DATABASE_HOST", "localhost")
db_port = os.environ.get("DATABASE_PORT", "5432")

# create the db URL for use in .session.py & the flask linking
URL = "postgresql://{}:{}@{}:{}/{}".format(db_user, db_pass, db_host, db_port, db_name)

# make the engine
engine = create_engine(URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def init():
    metadata.create_all(bind=engine)
