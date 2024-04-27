import json
import re
import logging
import yt_dlp
import time
import urllib
import socket
import threading
import audioread
import requests
import traceback

from datetime import datetime, timedelta
from yt_dlp import YoutubeDL


from Audio import AudioQueue, AudioValue
from telegram import Update
from telegram.ext import Filters, Updater
from telegram.ext import CallbackContext, CommandHandler, MessageHandler
import os

src = os.path.dirname(os.path.realpath(__file__))

ydl_opts = {"quiet": True}
youtube_dl_manager = yt_dlp.YoutubeDL(ydl_opts)


f = open(src + "/../config.json", "r")
config = json.load(f)
f.close()

BOT_USERNAME = config["username"]
MAX_VOLUME = 100

# check if url is youtube vid
YOUTUBE_REGEX = "^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$"
RAW_REGEX = "^.*(?=\.wav$|\.mp3$)"
TYPE_REGEX = "\.mp3"
URL_REGEX = "^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$"
STALE_TIMEOUT = 120

# config bot
updater = Updater(config["token"], use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# config audio queue
QUEUE = AudioQueue(updater.bot)


def test_length(url):
    time = 0
    ext = re.search(TYPE_REGEX, url)
    if ext is None:
        return time
    ext = ext.group(0)
    name = f"temp{ext}"
    try:
        with open(name, "wb") as f:
            doc = requests.get(url)
            f.write(doc.content)
        with audioread.audio_open(name) as f:
            # totalsec contains the length in float
            time = f.duration
    except:
        # just to make sure the file gets removed if its created
        pass
    os.remove(name)
    return int(time)


def is_quiet_hour():
    now = datetime.today()
    day = now.weekday()
    start = datetime.today()
    end = datetime.today()
    if day in [0, 1, 2, 3, 4]:
        start = now.replace(hour=0, minute=0)
        end = now.replace(hour=7, minute=0)
    else:
        start = now.replace(hour=2, minute=0)
        end = now.replace(hour=7, minute=0)
    return start <= now and now <= end


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

# garbage socket listener for quiet hour start


def quiet_wrapper():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            with conn:
                if addr[0] == "127.0.0.1":
                    while True:
                        data = conn.recv(1024)
                        if data == b"sush":
                            conn.sendall(data)
                            QUEUE.set_volume(0)
                            break
                        elif data == b"wake" and not is_quiet_hour():
                            conn.sendall(data)
                            QUEUE.set_volume(20)
                            break
                        break


def usage_dispatcher(message, update):
    return lambda: updater.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode="HTML"
    )


def start(update: Update, context: CallbackContext):
    # start command
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


def handler_handler(handler):
    # garbage filter to avoid crashing
    def callback(update: Update, context: CallbackContext):
        try:
            if (
                datetime.now().timestamp() - update.message.date.timestamp()
                > STALE_TIMEOUT
            ):
                return

            admin = str(update.message.from_user.id) in config["admins"]
            if (
                not admin
                and not str(update.effective_chat.id) == config["farther_chat_id"]
            ):
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You can only use this bot in the Farthest chat.",
                )
                return

            handler(update, context)
        except Exception as e:
            traceback.print_exc()
            for admin in config["admins"]:
                updater.bot.send_message(chat_id=admin, text=e.__str__())

    return callback


def add_callback(update: Update, context: CallbackContext):
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/add song\n\tsong: a youtube video link, or search term", update
    )

    # check if url is youtube link, if so add to queue
    if len(context.args) < 1:
        usage()
        return

    yt_match = re.match(YOUTUBE_REGEX, context.args[0])
    raw_match = re.match(RAW_REGEX, context.args[0])
    url_match = re.match(RAW_REGEX, context.args[0])
    # sp_match = re.match(SPOTIFY_REGEX, context.args[0])

    if yt_match:
        youtube_search_add(yt_match.group(0), url=True, update=update)
    elif raw_match and url_match:
        raw_add(context.args[0], update=update)
    else:
        term = " ".join(context.args)
        youtube_search_add(term, update=update)


def raw_add(phrase, update=None):
    audio = AudioValue(
        phrase,
        None,
        phrase,
        update.message.from_user.full_name,
        test_length(phrase),
        update.message.from_user.id,
    )
    audio.type = "RAW"
    QUEUE.add_audio(audio)


def youtube_search_add(term, url=False, update=None):
    result = youtube_search(term, url=url, update=update)

    # TODO add result
    audio = AudioValue(
        result["webpage_url"],
        result["thumbnail"],
        result["title"],
        update.message.from_user.full_name,
        result["duration"],
        update.message.from_user.id,
    )
    QUEUE.add_audio(audio)

    return result


def youtube_search(term, amount=1, url=False, update=None):
    """
    use yt_dlp to find the first non livestream youtube
    video, and return the important attributes

    if you want to print for debug you have to do
    this to get actual json:
        print(json.dumps(ydl.sanitize_info(info)))
    """
    ydl_opts = {
        "match_filter": yt_dlp.utils.match_filter_func("!is_live"),
        "noplaylist": "True" if url else "False",
        "format": "worstaudio/worst",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = {}
        out_vid = {"placeholder": True}
        if url:
            info = ydl.extract_info(url=term, download=False)
            if "_type" in info and info["_type"] == "playlist":
                results = []
                for entry in info["entries"]:
                    results += [
                        youtube_search_add(
                            entry["webpage_url"], url=True, update=update
                        )
                    ]
                return {"result": "ok", "type": "playlist", "list": results}
            else:
                out_vid = info
        else:
            info = ydl.extract_info(f"ytsearch{amount}:{term}", download=False)

            for entry in info["entries"]:
                if not entry["is_live"]:
                    out_vid = entry
                    break

            if amount > 20:
                return {
                    "result": "err",
                    "description": "All videos parsed for this search term were livestreams.",
                }
            elif "placeholder" in out_vid:
                return youtube_search(term, amount=amount + 5, update=update)

        out = {
            "result": "ok",
            "type": "video",
            "webpage_url": out_vid["webpage_url"],
            "thumbnail": out_vid["thumbnail"],
            "title": out_vid["title"],
            "duration": out_vid["duration"],
        }
        return out


def spotify():
    # TODO allow playing spotify songs
    pass


def volume_callback(update: Update, context: CallbackContext):
    # just commented out so u can change the volume at all times
    # if is_quiet_hour():
    #     if not str(update.message.from_user.id) in config["admins"]:
    #         context.bot.send_message(chat_id=update.effective_chat.id,
    #                                  text=f"You cannot adjust the volume during quiet hours.",
    #                                  parse_mode="HTML",
    #                                  reply_to_message_id=update.message.message_id)
    #         return

    usage = usage_dispatcher(
        "<b>Usage:</b>\n/volume [level [-d | -u]]\n\tVolume must be an integer from 0-100\n\t-d makes the volume go down by level\n\t -u makes the volume go up by level",
        update,
    )

    if len(context.args) == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"The current volume is {QUEUE.volume}%",
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id,
        )
        return
    if len(context.args) != 1:
        usage()
    value = int(context.args[0])
    if value <= MAX_VOLUME:
        QUEUE.set_volume(value)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Volume set to {value}%",
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id,
        )
    else:
        usage()


def mute_callback(update: Update, context: CallbackContext):
    usage = usage_dispatcher("<b>Usage:</b>\n/mute", update)

    if len(context.args) != 0:
        usage()
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Muted farther. use /volume to give farther a voice again",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )
    QUEUE.set_volume(0)


def pause_callback(update: Update, context: CallbackContext):
    QUEUE.pause()

    current = QUEUE.currently_playing
    if not current:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"There is nothing currently queued, use /add to add things to the queue.",
            reply_to_message_id=update.message.message_id,
        )
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Paused <a href='{QUEUE.currently_playing.url}'>{QUEUE.currently_playing.title}</a>. \n/play to resume.",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )


def play_callback(update: Update, context: CallbackContext):
    QUEUE.play()
    current = QUEUE.currently_playing
    if not current:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"There is nothing currently queued, use /add to add things to the queue.",
            reply_to_message_id=update.message.message_id,
        )
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Playing <a href='{current.url}'>{current.title}</a>.\n/pause to pause.",
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )


def skip_callback(update: Update, context: CallbackContext):
    admin = str(update.message.from_user.id) in config["admins"]
    if admin:
        if len(context.args) > 1:
            try:
                num = int(context.args[1])
                for _ in range(num):
                    QUEUE.skip()
            except:
                pass
    skipped = QUEUE.skip()
    text = (
        f"Skipped <a href='{skipped.url}'>{skipped.title}</a>."
        if skipped != None
        else "The queue is empty, there is nothing to skip. Add things to the queue with /add"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )


def queue_callback(update: Update, context: CallbackContext):
    if len(context.args) != 0:
        add_callback(update, context)
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=QUEUE.queue_to_string(),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id,
    )


def init_handlers():
    # setup all handlers
    dispatcher.add_handler(CommandHandler(["add", "a"], handler_handler(add_callback)))
    dispatcher.add_handler(CommandHandler("pause", handler_handler(pause_callback)))
    dispatcher.add_handler(CommandHandler("play", handler_handler(play_callback)))
    dispatcher.add_handler(CommandHandler("skip", handler_handler(skip_callback)))
    dispatcher.add_handler(
        CommandHandler(["queue", "q"], handler_handler(queue_callback))
    )
    dispatcher.add_handler(
        CommandHandler(["volume", "v"], handler_handler(volume_callback))
    )
    dispatcher.add_handler(CommandHandler("mute", handler_handler(mute_callback)))


def connect():
    # cursed connection check
    try:
        urllib.request.urlopen("https://www.google.com")
        return True
    except Exception as e:
        return False


if __name__ == "__main__":
    init_handlers()
    quiet_thread = threading.Thread(
        target=quiet_wrapper,
    )
    quiet_thread.start()
    print("Checking network connection...")
    while True:
        if connect():
            print("\tConnected")
            if is_quiet_hour():
                QUEUE.set_volume(0)
            updater.start_polling()
            break
        else:
            print("\tretry in 5")
            time.sleep(5)
