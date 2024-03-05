from sqlalchemy import Column, Integer, BigInteger, Boolean
from sqlalchemy.orm import relationship
from database.base import Base


class Users(Base):
    """
    User db table for storing information abt users


    id:             int, unique id for the model
    telegram_id:    int, telegram id of the user (string cause tel)
    admin:          bool, if the user is an admin (most will be an admin based oon
                        their chat status but why not build for extra functionality)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    # telegram ids can be held in a 64 bit signed int for sure
    telegram_id = Column(BigInteger)
    mute = Column(Boolean)
    admin = Column(Boolean)

    @staticmethod
    def find_or_create(telegram_id, session=None):
        """
        find a user by their telegram_id if they exist,
        if they do not exist then create a record and return it
        """
        # TODO

    @staticmethod
    def update(telegram_id, mute=None, session=None):
        # TODO maybe generalize an update method across these classes
        # would be nice if the class interface built into sqlalchemy works but
        # im not sure it does cause of linking to flask-sqlalchemy
        """
        simple update query wrapper
        """
        # TODO
