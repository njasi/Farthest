from streaming.Channel import Channel


def load_channels():
    """
    # TODO load from config or load from database?
    """

    print("Loading Channels")

    channel1 = Channel(channel_id=1, host="localhost", port=8085)
    return {1: channel1}


CHANNELS = load_channels()
