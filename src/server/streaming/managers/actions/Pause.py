from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager


class Pause(ChannelAction):
    """
    action for pausing
    """

    def run(self, chan: ChannelManager):
        chan.pause()

