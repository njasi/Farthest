import argparse
import random
import time
from telegram import Update

from downloaders.exceptions import NoDownloaderFound
from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args
from streaming.managers import Add

# make arg parser
parser = ArgumentParser(description="Add items to the queue")
parser.add_argument("term", nargs="+", help="your search term")
parser.add_argument(
    "-s",
    "--source",
    default="yt",
    choices=["yt", "test"],
    help="the source you want to download from",
)
parser.add_argument(
    "-r",
    "--random",
    required=False,
    default=False,
    action=argparse.BooleanOptionalAction,
    help="randomly select a result instead of top result",
)


async def add(update: Update, context: FartherContext):
    """
    Handler to deal with the add command

    /add [term | url] - add the thing to the queue
    """

    options = parse_args(parser, context)
    # print(options)

    # TODO detect term vs url

    term = " ".join(options.term)

    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='<b>Searching "<code>{}</code>" with {}</b>'.format(term, options.source),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )

    # TODO probably make the steps below run in a seperate thread
    results = context.search(term, flag=options.source)

    to_add = None
    if options.random:
        to_add = random.choice(results)
    else:
        to_add = results[0]

    # TODO remove this, just to test time delay of searching etc
    time.sleep(2)

    await context.bot.edit_message_text(
        "<b>Found</b> <a href='{}'>{}</a>".format(to_add.url, to_add.title),
        parse_mode="HTML",
        disable_web_page_preview=True,
        message_id=message.id,
        chat_id=message.chat_id,
    )

    # add user id to the video and send it to the channel
    to_add.user_id = update.effective_user.id
    context.farther_channel.send_action(Add(update, context, video=to_add))

    return
