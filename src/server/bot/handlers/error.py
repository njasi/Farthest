import os
import html
import json
import traceback
import logging
import asyncio
import tempfile

from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode

from bot.handlers.helpers import ParserError
from bot.FartherContext import FartherContext


TELEGRAM_MESSAGE_CHAR_LIMIT = 4096
DEVELOPER_CHAT_ID = os.environ["FARTHER_ADMIN_CHAT_ID"]

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def send_error_file(message, bot):
    """
    Send the error message as a file (used when its too long)
    - made so the temp file isnt deleted before the request
    """

    with tempfile.TemporaryFile("r+") as file:
        file.write(message)
        file.flush()
        file.seek(0)

        time_str = str(datetime.now()).replace(" ", "_")

        await bot.send_document(
            caption="An exception was raised while handling an update.\n\nHowever it was too long to send as a message, check the logs or the attached file.",
            parse_mode=ParseMode.HTML,
            chat_id=DEVELOPER_CHAT_ID,
            document=file,
            filename=f"ERROR_{time_str}.html",
        ),


def send_error(
    error: Exception, update: Update = None, context=None, bot=None, loop=None
):
    """
    Send an error to the admin chat, made here so other parts of the
    code can report an error with no ref to the bot

    error:      the error in question
    update:     the update which triggered the error (if any)
    context:    the context if any
    bot:        bot to use
    """

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)
    print(tb_string)

    message = "An exception was raised"
    if update is not None:
        update_str = update.to_dict() if isinstance(update, Update) else str(update)

        message += (
            "while handling an update:\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
        )
    else:
        message += ":\n"

    if context is not None:
        message += (
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        )
        if bot is None:
            bot = context.bot

    message += f"<pre>{html.escape(tb_string)}</pre>"

    if bot is None:
        print("No bot found...")
        return

    if loop is None:
        loop = asyncio.get_running_loop()

    if len(message) > TELEGRAM_MESSAGE_CHAR_LIMIT:
        # if too long send as file lol
        loop.call_soon_threadsafe(asyncio.ensure_future, send_error_file(message, bot))
        return

    # Finally, send the message
    loop.call_soon_threadsafe(
        asyncio.ensure_future,
        bot.send_message(
            chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
        ),
    )


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

    try:
        # rollback the session so no malformed changes save
        context.session.rollback()
    except Exception as e:
        # TODO may even want to exit the program right here
        logger.error("Error rolling back the session... uh oh:", exc_info=e)

    send_error(context.error, update=update, context=context)
