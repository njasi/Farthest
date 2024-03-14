from sqlalchemy import Column, Integer, String, Boolean
from .base import Base


class Channels(Base):
    """
    Channel db table for storing a list of the channels

    maybe in the future this is dynamic or smth


    id:             int, unique id for the channel item
    title:          string, the title of the channel
    flag:           string, short name to interact with the channel in commands
    description:    string, a short description of the channel
    hostname:       string, the hostname of the server its being streamed on
    port:           int, the port this is being streamed on
    local:          bool, if the channel is local to the bot/web server
    """

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    flag = Column(String)
    descrption = Column(String)

    # channelmanager type
    manager_type = Column(String, default="basic")

    # streaming location settings
    hostname = Column(String)
    port = Column(Integer)

    # not used right now but here for future support maybe
    local = Column(Boolean, default=True)

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
