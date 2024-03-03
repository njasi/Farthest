from telegram.ext import Application, ContextTypes
from telegram import Update

from streaming import CHANNELS, CHANNEL_FARTHER_ID, Channel
from downloaders import DOWNLOADERS, lookup, search
from database.users import Users


class FartherContext(ContextTypes.DEFAULT_TYPE):
    """
    Custom class to include channel objects and available downloaders as context properties
    """

    def __init__(
        self,
        application: Application,
        chat_id: int = None,
        user_id: int = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)

        # for now we dont really need other channels ig
        self.farther_channel: Channel = CHANNELS[CHANNEL_FARTHER_ID]

        # search the downloaders
        self.search = search

    @classmethod
    def from_update(cls, update: object, application: Application) -> "FartherContext":
        """Override from_update to ensure user exists in the db"""
        # Make sure to call super()
        context = super().from_update(update, application)

        if isinstance(update, Update) and update.effective_user:
            # ensure the user exists & attach them to context
            context.dbuser = Users.ensure_exists(update.effective_user.id)

        # Remember to return the object
        return context
