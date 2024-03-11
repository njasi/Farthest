from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager


class Skip(ChannelAction):
    """
    action for skipping currently playing
    """

    def __init__(self, amount) -> None:
        super(self, {amount})

    def run(self, chan: ChannelManager):
        chan.skip(self.amount)
