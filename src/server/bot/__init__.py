#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults

from .FartherContext import FartherContext
from .handlers.error import error_handler
from .handlers.start import start
from .handlers.add import add
from .handlers.queue import queue
from .handlers.pause import pause
from .handlers.play import play
from .handlers.skip import skip
from .handlers.remove import remove


# load in the needed constants
TOKEN = os.environ["BOT_TOKEN"]

# the app running the bot
APPLICATION = None


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
    application.add_handler(CommandHandler(["pause"], pause))
    application.add_handler(CommandHandler(["play"], play))
    application.add_handler(CommandHandler(["skip"], skip))
    application.add_handler(CommandHandler(["remove"], remove))
    # the error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    return application


if __name__ == "__main__":
    APPLICATION = launch()
