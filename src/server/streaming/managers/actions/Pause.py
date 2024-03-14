import logging
import asyncio
from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

import datetime

logger = logging.getLogger(__name__)


class Pause(ChannelAction):
    """
    action for pausing
    """

    def run(self, chan: ChannelManager):
        logger.info(
            f"[Channel {chan.channel_id}]: user(tid={self.update.effective_user.id}) paused"
        )

        paused_playback = chan.pause()
        curr = chan.get_current(session=self.session)

        if curr is None:
            self.text = (
                "The queue is empty, add items to the queue with /add."
            )
        else:
            details = (
                "<a href='{curr.history.video.url}'>{curr.history.video.title}</a> "
                f"({datetime.timedelta(seconds=chan.streamer.get_progress())}/"
                f"{datetime.timedelta(seconds=curr.history.video.length)})"
            )
            if paused_playback:
                self.text = (
                    f"<b>Paused 'Song':</b>\n{details})"
                    "\n\nTo resume playback use /play"
                )
            else:
                self.text = (
                    f"<b>Already Paused</b>\n<a href='{details})"
                    "\n\nIf there is no audio maybe the client needs to be refreshed."
                )

        self.send()
