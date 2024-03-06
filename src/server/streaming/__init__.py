from .managers import ChannelManager
from database import Session, Channels

CHANNEL_FARTHER_ID = 0
CHANNELS = {}


def init():
    """
    Intialize all of the backend streaming stuff,
     - channel class instances etc
    """
    load_channels()

def load_channels():
    """
    load the channels from the database
    """
    global CHANNELS
    print("Loading Channels...")

    channels = []

    with Session() as session:
        channels = session.query(Channels).all()

    channel_map = {}
    for channel in channels:
        channel_map[channel.id] = ChannelManager(
            channel_id=channel.id,
            host=channel.hostname,
            title=channel.title,
            port=channel.port,
        )
        # start worker threads
        channel_map[channel.id].start_channel()

    CHANNELS = channel_map
