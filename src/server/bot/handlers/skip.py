import logging
import asyncio
from telegram import Update

from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, parse_args
from streaming import CHANNELS
from streaming.managers import Skip

logger = logging.getLogger(__name__)

# make arg parser
parser = ArgumentParser(description="Skip the currently playing video")
parser.add_argument(
    "-c",
    "--channel",
    default="farther",
    choices=[key for key in CHANNELS],
    type=str,
    help="The flag of what channel you want to skip in.",
)


async def skip(update: Update, context: FartherContext):
    """
    Skip the selected channel
    """
    options = parse_args(parser, context)

    # NOTE: we attached the channels back in the FartherContext
    channel = context.channels[options.channel]

    channel.send_action(
        Skip(
            update,
            context,
            loop=asyncio.get_event_loop(),
        )
    )
