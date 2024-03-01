from streaming.Channel import Channel

CHANNEL_FARTHER_ID = 0


def load_channels():
    """
    # TODO load from config or load from database?
    """

    print("Loading Channels")

    channel0 = Channel(channel_id=1, host="localhost", pretty_name="Farther", port=8085)

    # start worker threads
    channel0.start_channel()

    return {0: channel0}


CHANNELS = load_channels()
