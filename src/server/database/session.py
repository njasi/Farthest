"""
This is meant to be a session generator that we can use
with the telegram bot portion of the code
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from server.database.meta import metadata
from . import URI

# make the engine
engine = create_engine(URI)

Session = sessionmaker(engine)

# example query with session
# note that this has to be used
# with Session.begin() as session:
    # jobs = session.query("Model here").all()
    # session.close()

