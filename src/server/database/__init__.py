import os
# import all the models 
from .models import *


db_name = os.environ.get("DATABASE_NAME", "farther")
db_user = os.environ.get("DATABASE_USER", "farther_user")
db_pass = os.environ.get("DATABASE_PASS", "password")
db_host = os.environ.get("DATABASE_HOST", "localhost")
db_port = os.environ.get("DATABASE_PORT", "5432")

# create the db URI for use in .session.py & the flask linking
URI = "postgresql://{}:{}@{}:{}/{}".format(db_user, db_pass, db_host, db_port, db_name)