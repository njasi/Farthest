import argparse
import random
import time
from telegram import Update

from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args

from downloaders import list_flags, search, Result, DOWNLOADER_MAP
from downloaders.exceptions import NoDownloaderFound
from streaming.managers import Add
from database import Video

# make arg parser
parser = ArgumentParser(description="Add items to the queue")
parser.add_argument("term", nargs="+", help="your search term")
parser.add_argument(
    "-s",
    "--source",
    default="yt",
    choices=list_flags(),
    help="the source you want to download from",
)
parser.add_argument(
    "-a",
    "--amount",
    default=1,
    type=int,
    choices=range(1, 21),
    help="amount of results you want to search",
)
parser.add_argument(
    "-r",
    "--random",
    required=False,
    default=False,
    action=argparse.BooleanOptionalAction,
    help="randomly select a result instead of top result.",
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
        text='<b>Searching:</b> \n"<code>{}</code>" on {}'.format(
            term, DOWNLOADER_MAP[options.source].site_name
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )

    # TODO probably make the below steps run in a seperate thread

    results = search(term, flag=options.source, amount=options.amount)

    to_add = results[0]
    if options.random:
        to_add = random.choice(results)

    await context.bot.edit_message_text(
        "<b>Found Video:</b> \n<a href='{}'>{}</a>".format(to_add.url, to_add.title),
        parse_mode="HTML",
        disable_web_page_preview=True,
        message_id=message.id,
        chat_id=message.chat_id,
    )

    # add the result to the video database and then pass it to the
    # channel manager, which will
    #   - make a history object
    #   - add it to the channel's queue
    # NOTE: if it's already there it just updates the db entry
    video = Video.add_result(result=to_add, session=context.session)

    # make the action and pass along to the channel manager
    action = Add(update, context, message_id=message.chat_id, video=video)
    context.farther_channel.send_action(action)

    return
