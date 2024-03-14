import logging

from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

logger = logging.getLogger(__name__)


from .Skip import list_skipped

class Skip(ChannelAction):
    """
    Action for skipping currently playing
    """

    def __init__(self, update, context, loop, amount: int) -> None:
        """
        amount:     int, the amount of items to skip

        # TODO go through and standardize this kinda
        """
        self.update = update
        self.context = context
        self.loop = loop
        self.amount = amount

        self.error_text = "There was an error skipping this 'song'."

        super(self)

    def run(self, chan: ChannelManager):
        removed = chan.remove(self.amount)

        if len(skipped) == 0:
            self.text = (
                f"<b>The queue is empty, there is no song to skip.</b>\n\n"
                "Add 'songs' to the queue with /add"
            )
        elif len(skipped) == 1:
            self.text = f"<b>Skipped 'Song'</b>:\n\n{list_skipped(skipped,bullet='')}"
        else:
            self.text = (
                f"<b>Skipped {len(skipped)} 'Songs'</b>:\n\n{list_skipped(skipped)}"
            )

        self.send()
