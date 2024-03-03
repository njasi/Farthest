"""
Setup the flash_sqlalchemy db from the metadata
made by the database module.
"""
from flask_sqlalchemy import SQLAlchemy

from database import metadata

db = SQLAlchemy(metadata=metadata)