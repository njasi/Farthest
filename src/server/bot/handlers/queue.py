import argparse
from telegram import Update

from streaming import CHANNELS

from bot import FartherContext
from bot.handlers.add import parser as add_parser, add
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args

# make arg parser
parser = ArgumentParser(description="Add items to the queue")
parser.add_argument(
    "-p",
    "--page",
    default=None,
    type=int,
    help="The page of the queue you want to check.",
)
parser.add_argument(
    "-s",
    "--start",
    default=0,
    type=int,
    help="The index of the video you want to start the listing at.",
)
parser.add_argument(
    "-c",
    "--channel",
    default="farther",
    choices=[key for key in CHANNELS],
    type=str,
    help="The flag of what channel you want to check",
)
parser.add_argument(
    "-a",
    "--all",
    required=False,
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Show all of the queue at once",
)


async def queue(update: Update, context: FartherContext):
    """
    Handler to deal with the queue command
    """

    # cursed here, dont look at it too hard

    options = None
    try:
        options = parse_args(parser, context)
        text = context.farther_channel.queue_to_telegram(**options.__dict__)
        await context.bot.send_message(
            text=text,
            chat_id=update.effective_chat.id,
            disable_web_page_preview=True,
        )
    except ParserError as og:
        try:
            # if the args are good for add handler just do that instead lol
            parse_args(add_parser, context)
            await add(update, context)
            return
        except ParserError:
            # assume the query was for the /queue command for now
            raise og
