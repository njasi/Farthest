from telegram.ext import (
    Application,
    CallbackContext,
)

from streaming import CHANNELS
from downloaders import DOWNLOADERS, lookup


class FartherContext(CallbackContext):
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
        self.channels = CHANNELS
        self.downloaders = DOWNLOADERS
        self.lookup = lookup
