from .managers import ChannelManager
from database import Session, Channels
import logging

logger = logging.getLogger(__name__)

# static farther flag
CHANNEL_FARTHER_FLAG = "farther"

CHANNELS = {}


def init():
    global CHANNELS
    """
    Intialize all of the backend streaming stuff,
     - load the channel db into their managers
    """
    CHANNELS = load_channels()


def load_channels():
    """
    load the channels from the database
    """
    logger.info("Loading Channels...")

    channels = []

    with Session() as session:
        channels = session.query(Channels).all()

    channel_map = {}
    for channel in channels:
        channel_map[channel.flag] = ChannelManager(
            channel_id=channel.id,
            host=channel.hostname,
            title=channel.title,
            flag=channel.flag,
            port=channel.port,
        )
        # start worker threads
        channel_map[channel.flag].start_channel()

    return channel_map
