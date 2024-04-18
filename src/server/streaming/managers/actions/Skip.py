import logging
import asyncio
import datetime

from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

logger = logging.getLogger(__name__)


def list_skipped(skipped, bullet="-"):
    """
    turn a list of skipped videos into a presentable html formmatted
    string
    """
    res = []
    for s in skipped:
        res += [s.telegram_str(bullet=bullet, length=False).strip()]

    return "\n".join(res)


class Skip(ChannelAction):
    """
    Action for skipping currently playing
    """

    def __init__(self, update, context, loop, amount: int) -> None:
        """
        amount:     int, the amount of items to skip

        # TODO go through and standardize this kinda
        """
        super().__init__(update, context, loop)
        self.amount = amount

        self.error_text = "There was an error skipping this 'song'."

    def run(self, chan: ChannelManager):
        skipped = chan.skip(self.session, amount=self.amount)

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
