import logging

from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

logger = logging.getLogger(__name__)


from .Skip import list_skipped


class Remove(ChannelAction):
    """
    Action for skipping currently playing
    """

    def __init__(self, update, context, loop, idx: int) -> None:
        """
        amount:     int, the amount of items to skip

        # TODO go through and standardize this kinda
        """
        super().__init__(update, context, loop)
        self.idx = idx

        self.error_text = "There was an error removing this 'song'."


    def run(self, chan: ChannelManager):
        removed = chan.remove(self.idx)

        if len(removed) == 0:
            self.text = (
                f"<b>There is no 'song' at position {self.idx} of the queue.</b>\n\n"
                "Use the /queue command to see the positions. Note that it is 0-indexed."
            )
        else:
            self.text = f"<b>Removed 'Song'</b>:\n\n{list_skipped(removed,bullet='')}"

        self.send()
