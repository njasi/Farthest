import logging
import asyncio
import datetime
from .ChannelAction import ChannelAction
from ..BasicManager import BasicManager as ChannelManager

logger = logging.getLogger(__name__)


class Play(ChannelAction):
    """
    action for playing stream
    """

    def run(self, chan: ChannelManager):
        logger.info(
            f"[Channel {chan.channel_id}]: user(tid={self.update.effective_user.id}) played"
        )

        # TODO do an extra check for if the channel is stuck (ie no current, but the queue is not empty)
        started_playback = chan.play()
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
            if started_playback:
                message = (
                    f"<b>Played 'Song':</b>\n{details})\n\nTo pause playback use /pause"
                )
            else:
                message = (
                    f"<b>Already Playing 'song'</b>\n{details}"
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
