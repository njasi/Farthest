import json
import re
import logging
import youtube_dl
import time
import urllib


from youtube_dl import YoutubeDL
from Audio import AudioQueue, AudioValue
from telegram import Update
from telegram.ext import Filters, Updater
from telegram.ext import CallbackContext, CommandHandler, MessageHandler
import os
src = os.path.dirname(os.path.realpath(__file__))

ydl_opts = {
    'quiet': True
}
youtube_dl_manager = youtube_dl.YoutubeDL(ydl_opts)


f = open(src + "/../config.json", "r")
config = json.load(f)
f.close()

BOT_USERNAME = config["username"]
MAX_VOLUME = 100

# check if url is youtube vid
YOUTUBE_REGEX = '^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$'

# config bot
updater = Updater(config["token"], use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# config audio queue
QUEUE = AudioQueue(updater.bot)


def usage_dispatcher(message, update):
    return lambda: updater.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode="HTML")


def start(update: Update, context: CallbackContext):
    # start command
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!")


def handler_handler(handler):
    # garbage filter to avoid crashing
    def callback(update: Update, context: CallbackContext):
        # try:
        handler(update, context)
        # except Exception as e:
        #     updater.bot.send_message(
        #         chat_id=config["admins"][0], text=e.__str__())
    return callback


def add_callback(update: Update, context: CallbackContext):
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/add song\n\tsong: a youtube video link, or search term", update)

    # check if url is youtube link, if so add to queue
    if len(context.args) < 1:
        usage()
        return

    yt_match = re.match(YOUTUBE_REGEX, context.args[0])
    # sp_match = re.match(SPOTIFY_REGEX, context.args[0])
    # raw_match = re.match(RAW_MATCH, context.args[0])
    if yt_match:
        options = {
            'format': 'worstaudio/worst',
            'keepvideo': False,
        }
        video_info = YoutubeDL(options).extract_info(
            url=yt_match.group(0),
            download=False
        )

        # file = open("test.txt", "w")
        # file.write(str(video_info))
        # file.close()

        audio = AudioValue(
            yt_match.group(0),
            video_info["thumbnail"],
            video_info["title"],
            update.message.from_user.full_name,
            video_info["duration"],
            update.message.from_user.id)
        QUEUE.add_audio(audio)

    else:
        options = {'format': 'worstaudio/worst', 'noplaylist': 'True'}
        term = " ".join(context.args)
        video_info = YoutubeDL(options).extract_info(
            f"ytsearch:{term}", download=False)['entries'][0]
        audio = AudioValue(
            video_info["webpage_url"],
            video_info["thumbnail"],
            video_info["title"],
            update.message.from_user.full_name,
            video_info["duration"],
            update.message.from_user.id)
        QUEUE.add_audio(audio)
    # elif



def spotify():
    # TODO allow playing spotify songs
    pass


def volume_callback(update: Update, context: CallbackContext):
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/volume [level]\n\tVolume must be an integer from 0-100", update)

    if len(context.args) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"The current volume is {QUEUE.volume}%",
                                 parse_mode="HTML",
                                 reply_to_message_id=update.message.message_id)
        return
    if len(context.args) != 1:
        usage()
    value = int(context.args[0])
    if value <= MAX_VOLUME:
        QUEUE.set_volume(value)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Volume set to {value}%",
                                 parse_mode="HTML",
                                 reply_to_message_id=update.message.message_id)
    else:
        usage()


def mute_callback(update: Update, context: CallbackContext):
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/mute", update)

    if len(context.args) != 0:
        usage()
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Muted farther. use /volume to give farther a voice again",
                             parse_mode="HTML",
                             disable_web_page_preview=True,
                             reply_to_message_id=update.message.message_id)
    QUEUE.set_volume(0)


def pause_callback(update: Update, context: CallbackContext):
    QUEUE.pause()

    current = QUEUE.currently_playing
    if not current:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"There is nothing currently queued, use /add to add things to the queue.",
                                 reply_to_message_id=update.message.message_id)
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Paused <a href='{QUEUE.currently_playing.url}'>{QUEUE.currently_playing.title}</a>. \n/play to resume.",
                             parse_mode="HTML",
                             disable_web_page_preview=True,
                             reply_to_message_id=update.message.message_id)


def play_callback(update: Update, context: CallbackContext):
    QUEUE.play()
    current = QUEUE.currently_playing
    if not current:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"There is nothing currently queued, use /add to add things to the queue.",
                                 reply_to_message_id=update.message.message_id)
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Playing <a href='{current.url}'>{current.title}</a>.\n/pause to pause.",
                             disable_web_page_preview=True,
                             parse_mode="HTML",
                             reply_to_message_id=update.message.message_id)


def skip_callback(update: Update, context: CallbackContext):
    skipped = QUEUE.skip()
    text = f"Skipped <a href='{skipped.url}'>{skipped.title}</a>." if skipped != None else "The queue is empty, there is nothing to skip. Add things to the queue with /add"
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text,
                             disable_web_page_preview=True,
                             parse_mode="HTML",
                             reply_to_message_id=update.message.message_id)


def queue_callback(update: Update, context: CallbackContext):
    if len(context.args) != 0:
        add_callback(update, context)
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=QUEUE.queue_to_string(),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id)


def init_handlers():
    # setup all handlers
    dispatcher.add_handler(CommandHandler(
        ['add', 'a'], handler_handler(add_callback)))
    dispatcher.add_handler(CommandHandler(
        'pause', handler_handler(pause_callback)))
    dispatcher.add_handler(CommandHandler(
        'play', handler_handler(play_callback)))
    dispatcher.add_handler(CommandHandler(
        'skip', handler_handler(skip_callback)))
    dispatcher.add_handler(CommandHandler(
        ['queue', 'q'], handler_handler(queue_callback)))
    dispatcher.add_handler(CommandHandler(
        ['volume', 'v'], handler_handler(volume_callback)))
    dispatcher.add_handler(CommandHandler(
        'mute', handler_handler(mute_callback)))


def connect():
    # cursed connection check
    try:
        urllib.request.urlopen('https://www.google.com')
        return True
    except:
        return False


if __name__ == "__main__":
    init_handlers()
    while True:
        if connect():
            print("connected")
            updater.start_polling()
            break
        else:
            print("retry in 5")
            time.sleep(5)
