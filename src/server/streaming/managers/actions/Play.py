
from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

class Play(ChannelAction):
    """
    action for playing stream
    """

    def run(self, chan: ChannelManager):
        chan.play()
