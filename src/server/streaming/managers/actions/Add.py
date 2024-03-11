import asyncio
import datetime
from telegram import LinkPreviewOptions

from error import send_error
from database import Video

from ..BasicManager import BasicManager as ChannelManager
from .ChannelAction import ChannelAction


class Add(ChannelAction):
    """
    action for adding to the queue

    update:         the telegram update that triggered this
    context:        the telegram context
    message_id:     id of the message to edit
    video_id:       the id of the video to add
    loop:           the aio loop the telegram bot is running in
    announce:       if a message should be edited
    """

    def run(self, chan: ChannelManager):
        # add the video instance to this session
        # could add by id with no issues if there r problems
        video = Video.find_by_id(self.video_id, session=self.session)

        # ask for the time before the new one is added
        time_until = chan.queue_get_length()
        queue = None

        try:
            queue = chan.add(video)

            # if the adding should not be announced, just return.
            # NOTE: (this happens when a playlist is added)
            # and maybe when added from webclient
            if not self.announce:
                return

        except Exception as e:
            send_error(e)

            self.loop.call_soon_threadsafe(
                asyncio.ensure_future,
                self.context.bot.edit_message_text(
                    text="There was an error adding this 'song' to the queue.",
                    chat_id=self.update.effective_chat.id,
                    message_id=self.message_id,
                    parse_mode="HTML",
                ),
            )
            return

        message = (
            f"<b>Added 'song'</b> (plays in {datetime.timedelta(seconds=time_until)})\n"
            f"<a href='{video.url}'>{video.title}</a>\n\n"
        )
        if video.stats.play_count == 0:
            message += "Congratulations you're the first person to queue this 'song'!"
        else:
            message += f"Play Count: {video.stats.play_count}"

        # TODO: if the song was just added to empty maybe dont send,
        #       cause playing will get sent
        self.loop.call_soon_threadsafe(
            asyncio.ensure_future,
            self.context.bot.edit_message_text(
                text=message,
                chat_id=self.update.effective_chat.id,
                message_id=self.message_id,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(
                    url=video.url,
                    prefer_small_media=True,
                ),
            ),
        )
