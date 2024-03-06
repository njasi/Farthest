from sqlalchemy import Column, Integer, String, Boolean
from .base import Base


class Channels(Base):
    """
    Channel db table for storing a list of the channels

    maybe in the future this is dynamic or smth


    id:             int, unique id for the channel item
    title:          string, the title of the channel
    description:    string, a short description of the channel
    hostname:       string, the hostname of the server its being streamed on
    port:           int, the port this is being streamed on
    local:          bool, if the channel is local to the bot/web server
    """

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    descrption = Column(String)

    # streaming location settings
    hostname = Column(String)
    port = Column(Integer)

    # not used right now but here for future support maybe
    local = Column(Boolean, default=True)
