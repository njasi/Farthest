from time import time
from telegram import Update
from telegram.ext import ContextTypes

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

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
        # for communicating with telegram if needed
        # most actions will be triggered by an update after all
        self.update = update
        self.context = context

        # session obj for this action
        self.session = Session()

        # additional info
        self.created_at = time()
        self.__dict__.update(**kwargs)

    def run(self, chan: ChannelManager):
        """
        implement for each action seperately
        """

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
