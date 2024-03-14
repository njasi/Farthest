import logging
import asyncio
from telegram import Update

from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, parse_args
from streaming import CHANNELS
from streaming.managers import Pause

logger = logging.getLogger(__name__)

# make arg parser
parser = ArgumentParser(description="Pause the stream")
parser.add_argument(
    "-c",
    "--channel",
    default="farther",
    choices=[key for key in CHANNELS],
    type=str,
    help="The flag of the channel you want to pause",
)


async def pause(update: Update, context: FartherContext):
    """
    Pause the selected channel
    """
    options = parse_args(parser, context)

    # NOTE: we attached the channels back in the FartherContext
    channel = context.channels[options.channel]

    channel.send_action(
        Pause(
            update,
            context,
            loop=asyncio.get_event_loop(),
        )
    )
