import html
import json
import traceback
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.handlers.helpers import ParserError, load_config
from bot.FartherContext import FartherContext


TELEGRAM_MESSAGE_CHAR_LIMIT = 4096
DEVELOPER_CHAT_ID = load_config("admin_chat_id")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: FartherContext) -> None:
    """Log the error and send a telegram message to notify the developers."""

    if isinstance(context.error, ParserError):
        await context.bot.sendMessage(
            update.effective_chat.id,
            text=context.error.message,
            parse_mode="HTML",
        )
        return

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)


    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)


    # rolback any half changes that may have happened cause of the error
    context.session.rollback()

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    if len(message) > TELEGRAM_MESSAGE_CHAR_LIMIT:
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text = "An exception was raised while handling an update\nHowever it was too long to send as a message, check the logs",
            parse_mode=ParseMode.HTML,
        )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )
