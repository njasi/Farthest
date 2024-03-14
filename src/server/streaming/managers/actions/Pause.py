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

        message = ""
        if curr is None:
            message = (
                "The queue is empty, add items to the queue with /add."
            )
        else:
            details = (
                "<a href='{curr.history.video.url}'>{curr.history.video.title}</a> "
                f"({datetime.timedelta(seconds=chan.streamer.get_progress())}/"
                f"{datetime.timedelta(seconds=curr.history.video.length)})"
            )
            if paused_playback:
                message = (
                    f"<b>Paused 'Song':</b>\n{details})"
                    "\n\nTo resume playback use /play"
                )
            else:
                message = (
                    f"<b>Already Paused</b>\n<a href='{details})"
                    "\n\nIf there is no audio maybe the client needs to be refreshed."
                )

        self.loop.call_soon_threadsafe(
            asyncio.ensure_future,
            self.context.bot.send_message(
                text=message,
                chat_id=self.update.effective_chat.id,
                reply_to_message_id=self.update.effective_message.id,
            ),
        )
