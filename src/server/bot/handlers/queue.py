import argparse
import random
import time
from telegram import Update

from downloaders.exceptions import NoDownloaderFound
from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args
from streaming.managers import Add
from bot.handlers.add import parser as add_parser, add

# make arg parser
parser = ArgumentParser(description="Add items to the queue")
parser.add_argument(
    "-p",
    "--page",
    default=0,
    help="the page of the queue you want to check",
)


async def queue(update: Update, context: FartherContext):
    """
    Handler to deal with the queue command
    """

    # cursed here, dont look at it too hard

    options = None
    try:
        options = parse_args(parser, context)
    except ParserError as og:
        try:
            # if the args are good for add handler just do that instead lol
            parse_args(add_parser, context)
            add(update, context)
            return
        except ParserError:
            # assume the query was for the /queue command for now
            raise og

    await context.bot.send_message(
        text = context.farther_channel.queue_to_html(),
        parse_mode = "HTML",
        chat_id = update.effective_chat.id,
    )
