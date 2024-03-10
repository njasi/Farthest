import time
from telegram import Update, LinkPreviewOptions
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from .BasicManager import BasicManager as ChannelManager
import asyncio


class ChannelAction:
    """
    class to bundle any channel action,
    idea is we pass it though to the thread in a queue of tasks

    id rather use a combined struct or smth but this is python so

    could pass a tuple but then the managing func would be rough
    with this we can pass values through & have distince actions

    and the worker thread processes them one by one
    """

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
        # for communicating with telegram if needed
        # most actions will be triggered by an update after all
        self.update = update
        self.context = context

        # additional info
        self.created_at = time.time()
        self.__dict__.update(**kwargs)

    def run(self, chan: ChannelManager):
        """
        implement for each action seperately
        """


class Pause(ChannelAction):
    """
    action for pausing
    """

    def run(self, chan: ChannelManager):
        chan.pause()


class Play(ChannelAction):
    """
    action for playing stream
    """

    def run(self, chan: ChannelManager):
        chan.play()


class Skip(ChannelAction):
    """
    action for skipping currently playing
    """

    def __init__(self, amount) -> None:
        super(self, {amount})

    def run(self, chan: ChannelManager):
        chan.skip(self.amount)


class Add(ChannelAction):
    "action for adding to the queue"

    def run(self, chan: ChannelManager):
        # ask for the time before the new one is added
        print(self.__dict__)
        time_until = chan.queue_get_length()

        # try:
        # TODO should return the new queue instance
        chan.add(self.video)
        # if the adding should not be announced, just return.
        # NOTE: (this happens when a playlist is added)
        if not self.announce:
            return
        
        # except Exception as e:
        #     raise e
        #     # TODO filter on
        #     #   age restriction error
        #     #   private video error
        #     #   other idk

        #     self.loop.call_soon_threadsafe(
        #         asyncio.ensure_future,
        #         self.context.bot.edit_message_text(
        #             text="There was an error adding this 'song' to the queue.",
        #             chat_id=self.update.effective_chat.id,
        #             message_id=self.message_id,
        #             parse_mode="HTML",
        #         ),
        #     )
        #     return

        message = f"<b>Added \"song\"</b>:\n<a href='{self.video.url}'>{self.video.title}</a>\n\n"

        if self.video.stats.play_count == 0:
            message += "Congratulations you're the first person to queue this 'song'!"
        else:
            message += f"Play Count: {self.video.stats.play_count}"

        # manager has already added the song so chop it

        # TODO if the song was just added to empty maybe dont send, cause playing will get sent
        self.loop.call_soon_threadsafe(
            asyncio.ensure_future,
            self.context.bot.edit_message_text(
                text=message,
                chat_id=self.update.effective_chat.id,
                message_id=self.message_id,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(
                    url=self.video.url,
                    prefer_small_media=True,
                ),
            ),
        )
