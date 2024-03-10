from sqlalchemy import Column, Integer, BigInteger, Boolean
from sqlalchemy.orm import relationship
from .base import Base


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
    telegram_id = Column(Integer)
    mute = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)

    @staticmethod
    def find_or_create(telegram_id, session=None):
        """
        find a user by their telegram_id if they exist,
        if they do not exist then create a record and return it
        """

        if session is None:
            raise ValueError("Session cannot be None")

        user = session.query(Users).filter_by(telegram_id=telegram_id).first()

        if user is None:
            # If the user does not exist, create a new entry
            user = Users(telegram_id=telegram_id)
            session.add(user)
            session.commit()

        return user

    @staticmethod
    def update(telegram_id, mute=None, admin=None, session=None):
        """
        simple update query wrapper,
        if not none update the values for the related user
        """
        # TODO

    def __str__(self):
        """
        General case __str__ method cause im tired of memory addrs in debug
        """
        res = f"{type(self).__name__}("
        # add attrs to ignore here
        ignore = []

        columns = [m.key for m in self.__table__.columns]

        for key in columns:
            if key not in ignore:
                res += f"\n\t{key} = {getattr(self, key)}"
        res += ")\n"
        return res
