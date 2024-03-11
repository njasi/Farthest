from time import time
from telegram import Update
from telegram.ext import ContextTypes

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

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
        # for communicating with telegram if needed
        # most actions will be triggered by an update after all
        self.update = update
        self.context = context

        # additional info
        self.created_at = time()
        self.__dict__.update(**kwargs)

    def run(self, chan: ChannelManager):
        """
        implement for each action seperately
        """
