import asyncio
from time import time
from telegram import Update
from telegram.ext import ContextTypes

from error import send_error
from database import Session
from ..BasicManager import BasicManager as ChannelManager


class ChannelAction:
    """
    class to bundle any channel action,
    idea is we pass it though to the thread in a queue of tasks

    id rather use a combined struct or smth but this is python so

    could pass a tuple but then the managing func would be rough
    with this we can pass values through & have distince actions

    and the worker thread processes them one by one
    """

    def __init__(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, loop, menu_id = None, **kwargs
    ):
        # for communicating with telegram if needed
        # most actions will be triggered by an update after all
        self.update = update
        self.context = context
        self.loop = loop

        # message text to send or edit at the end of the action
        self.text = ""
        # default error text to use
        self.error_text = "There was an error processing this action."
        self.send_args = {}

        # session obj for this action
        self.session = Session()

        # additional info
        self.created_at = time()
        self.__dict__.update(**kwargs)

    def run(self, chan: ChannelManager):
        """
        implement for each action seperately
        """

    def send_error(self, error, text=None):
        """
        Wrapper around send_error from .error & ChannelAction.send that
        makes it simple to report an error & update the user on it
        """
        if text is None:
            text = self.error_text
        send_error(error)
        self.send(text)

    def send(self, text=None):
        if text is not None:
            self.text = text

        if not hasattr(self, "loop"):
            return

        if self.loop is None:
            return

        if hasattr(self, "menu_id"):
            self.loop.call_soon_threadsafe(
                asyncio.ensure_future,
                self.context.bot.edit_message_text(
                    text=self.text,
                    message_id=self.menu_id,
                    chat_id=self.update.effective_chat.id,
                    **self.send_args
                ),
            )
            return

        self.loop.call_soon_threadsafe(
            asyncio.ensure_future,
            self.context.bot.send_message(
                text=self.text,
                chat_id=self.update.effective_chat.id,
                reply_to_message_id=self.update.effective_message.id,
                **self.send_args
            ),
        )

    def cleanup(self):
        self.session.close()

    def __del__(self):
        """
        happens when the class instance is being deleted by python,
        not very clean but it's simple and we're not too worried
        abt the speed of cleanup, just that it does happen

        since we control the liffecycle of the action instance,
        this is only in case of an error really
        """
        try:
            self.cleanup()
        except:
            pass
