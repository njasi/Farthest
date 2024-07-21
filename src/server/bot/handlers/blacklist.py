import logging
import argparse
import random
import time
import asyncio
from telegram import Update

from bot import FartherContext
from bot.handlers.helpers import ArgumentParser, ParserError, parse_args

from downloaders import DOWNLOADER_MAP, list_flags, search, lookup_url
from downloaders.Result import Result, TYPE_PLAYLIST, TYPE_LIVESTREAM
from downloaders.exceptions import NoDownloaderFound, FetchError

from streaming.managers import Add
from database import Video

logger = logging.getLogger(__name__)

# make arg parser
parser = ArgumentParser(description="Blacklist videos or search terms")
parser.add_argument("term", nargs="+", help="your search term")

async def add(update: Update, context: FartherContext):
    """
    Handler to deal with the blacklist command

    /blacklist [term | url] - thing to be blacklisted
    """

    options = parse_args(parser, context)

    term = " ".join(options.term)

    # TODO maybe make the below steps run in a seperate thread?

    try:
        # check if it matches any url regexes in the downloaders
        # if so, get the details of the url rather than doing a search
        downloader = lookup_url(term)
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b>Getting Link Details:</b> \nChecking {downloader.site_name}, if this is a link to a playlist this may take a bit.",
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id,
        )
        # attach the id to the context for error handling below
        context.menu_id = message.id

        details = downloader.get_details(term)

        if details.type == TYPE_PLAYLIST:
            await context.bot.edit_message_text(
                "<b>Found Playlist:</b> \n<a href='{}'>{}</a>\n\nLength: {}".format(
                    details.url, details.title, len(details.videos)
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
                message_id=message.id,
                chat_id=message.chat_id,
            )

            # if they selected random, pick one from the playlist
            if options.random:
                # sleep a sec or 2 so that the edits arent to jarring
                time.sleep(2)
                to_add = random.choice(details.videos)
                await add_video(
                    to_add, update, context, message, context.farther_channel
                )
                return

            # otherwise queue the entire playlist
            await add_playlist(
                details, update, context, message, context.farther_channel
            )

        elif details.type == TYPE_LIVESTREAM:
            # TODO make livestream?
            await context.bot.edit_message_text(
                f"<b>Found Livestream:</b>\n<a href='{details.url}'>{details.title}</a>\n\nUnfortunately farther does not support livestreams. If this is a feature you would like to see, you should request it with the /feedback command, so that the admins can ignore you.",
                parse_mode="HTML",
                disable_web_page_preview=True,
                message_id=message.id,
                chat_id=message.chat_id,
            )
            return

        else:
            # video or audio, so just add it with the method
            await add_video(details, update, context, message, context.farther_channel)

    except NoDownloaderFound:
        # no downloader, so not a match to any of the url regexes specfied,
        # thus do a search assuming it is a term
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'<b>Searching:</b> \n"<code>{term}</code>" on {DOWNLOADER_MAP[options.source].site_name}',
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_to_message_id=update.message.message_id,
        )

        results = search(term, flag=options.source, amount=options.amount)
        if len(results) == 0:
            await context.bot.edit_message_text(
                "<b>No Results Found...</b>",
                parse_mode="HTML",
                disable_web_page_preview=True,
                message_id=message.id,
                chat_id=message.chat_id,
            )
            return

        to_add = results[0]
        if options.random:
            to_add = random.choice(results)

        await add_video(to_add, update, context, message, context.farther_channel)

    except FetchError as e:
        """
        catch here so we can edit, but make sure to raise again so
        the error handler still gets it later.

        # TODO maybe attach a menu_id to the context optionally to edit it there?
        """
        await context.bot.edit_message_text(
            f"<b>Error Getting Link Details:</b>\n\n<pre>{e.msg}</pre>",
            message_id=context.menu_id,
            chat_id=update.effective_chat.id,
        )
        context.menu_id = None

        raise e

    return


async def add_video(
    result: Result,
    update,
    context,
    message,
    channel,
    header="Found Song",
    update_message=True,
):
    """
    Helper for adding a single video to the channel queue

    add the result to the video database and then pass it to the
    channel manager, which will
      - make a history object
      - add it to the channel's queue
    NOTE: if it's already there it just updates the db entry


    result:             the result from .search or .get_details that we are adding
    update:             the telegram update that triggered this
    context:            the telegram context
    message:            the message to edit when responding
    channel:            the channel to add the item to
    header:             the header of the message to put in bold
    update_message:     if the message should be edited
    """

    video = Video.add_result(result=result, session=context.session)

    # make the action and pass along to the channel manager
    if update_message:
        await context.bot.edit_message_text(
            f"<b>{header}:</b> \n<a href='{result.url}'>{ result.title}</a>",
            parse_mode="HTML",
            disable_web_page_preview=True,
            message_id=message.id,
            chat_id=message.chat_id,
        )

    channel.send_action(
        Add(
            update,
            context,
            loop=asyncio.get_event_loop(),
            menu_id=message.id,
            video_id=video.id,
            announce=update_message,
        )
    )


async def add_playlist(playlist: Result, update, context, message, channel):
    """
    Add a playlst to the queue

    playlist:   the result from .get_details that we are adding
    update:     the telegram update that triggered this
    context:    the telegram context
    message:    the message to edit when responding
    channel:    the channel to add the playlist to
    """

    await context.bot.edit_message_text(
        f"<b>Adding Playlist:</b> \n<a href='{playlist.url}'>{ playlist.title}</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        message_id=message.id,
        chat_id=message.chat_id,
    )

    time = 0
    for video in playlist.videos:
        time += video.length
        await add_video(video, update, context, message, channel, update_message=False)

    # TODO, add starts in n mins message
    await context.bot.edit_message_text(
        f"<b>Added Playlist:</b> \n<a href='{playlist.url}'>{playlist.title}</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        message_id=message.id,
        chat_id=message.chat_id,
    )
