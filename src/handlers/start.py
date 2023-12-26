from telegram import Update
from telegram.ext import ContextTypes
from database.history import add_song

START_STRING = '''TODO put meaningful text here'''


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays start information, see the string above."""

    add_song("sdffeifn", "TEST SONG", 19999)
    await update.effective_message.reply_html(START_STRING)
