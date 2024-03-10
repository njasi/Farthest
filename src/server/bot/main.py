#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults

from bot.FartherContext import FartherContext
from bot.handlers.start import start
from bot.handlers.add import add
from bot.handlers.queue import queue
from bot.handlers.helpers import load_config
from bot.handlers.error import error_handler


# load in the needed constants
TOKEN = load_config("token")


def launch() -> None:
    """Run the bot."""
    context_types = ContextTypes(context=FartherContext)
    application = (
        Application.builder()
        .token(TOKEN)
        .defaults(
            Defaults(
                parse_mode="HTML",
                allow_sending_without_reply=True,
            )
        )
        .context_types(context_types)
        .build()
    )

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["queue", "q"], queue))
    application.add_handler(CommandHandler(["add", "a"], add))
    # the error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    launch()
