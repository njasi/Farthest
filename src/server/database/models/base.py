"""
Init sqlalchem base model here, and then link it into
flask elsewhere with flask-sqlalchem so we can query from the bot & the
flask app. Kinda annoying, but it somewhat makes sense, as it's
vaguely reasonable to query the db locally for the bot, but that
feels wrong to me.
"""

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# import this when we wanna link into flask
metadata = MetaData()

Base = declarative_base(metadata=metadata)