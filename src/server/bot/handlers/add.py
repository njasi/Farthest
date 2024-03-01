import argparse
from telegram import Update

from downloaders.exceptions import NoDownloaderFound
from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args


from pprint import pprint

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

    searching_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Searching "<code>{}</code>" with {}'.format(term, options.source),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )

    print(context.downloaders)

    try:
        downloader = context.lookup(options.source)
    except NoDownloaderFound:
        print("No matching source found")
        return

    results = downloader.search(term)

    return
