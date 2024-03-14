import asyncio
import datetime
from telegram import LinkPreviewOptions
import logging

logger = logging.getLogger(__name__)

from error import send_error
from database import Video, Users

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
        video = Video.find_by_id(self.video_id, session=self.session)
        user = Users.find_or_create(self.update.effective_user.id, session=self.session)

        logger.info(
            f"[Channel {chan.channel_id}]: user({user.id}) added video({video.id})"
        )

        # ask for the time before the new one is added
        time_until = chan.queue_get_length()

        try:
            chan.add(video, user, self.session)

            # if the adding should not be announced, just return.
            # NOTE: (this happens when a playlist is added)
            if not self.announce:
                return

        except Exception as e:
            self.send_error(e, "There was an error adding this 'song' to the queue.")
            return

        self.text = (
            f"<b>Added 'song'</b> (plays in {datetime.timedelta(seconds=time_until)})\n"
            f"<a href='{video.url}'>{video.title}</a>\n\n"
        )
        if video.stats.play_count == 0:
            self.text += "Congratulations you're the first person to queue this 'song'!"
        else:
            self.text += f"Play Count: {video.stats.play_count}"

        # TODO: if the song was just added to empty maybe dont send,
        #       cause playing will get sent

        self.send_args = {
            "link_preview_options": LinkPreviewOptions(
                url=video.url,
                prefer_small_media=True,
            ),
        }
        self.send()
