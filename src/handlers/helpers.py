import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest


def load_config(key=None, config_path="./config.json"):
    """Load in the config file, or a var from the file"""
    with open(config_path) as file:
        data = json.load(file)
        if key is None:
            return data
        else:
            return data[key]


ADMINS = load_config(key="admins")
FARTHER_CHAT_ID = load_config(key="farther_chat_id")


def is_quiet_hour():
    '''
    Check if it is currently quiet hours,
    - after midnight on sun-thur
    - after 2am on fri-sat, sat-sun interfaces
    '''
    now, start, end = datetime.today(), datetime.today(), datetime.today()
    day = now.weekday()
    if day in [0, 1, 2, 3, 4]:
        # sun-thur
        start = start.replace(hour=0, minute=0)
        end = end.replace(hour=7, minute=0)
    else:
        start = start.replace(hour=2, minute=0)
        end = end.replace(hour=7, minute=0)
    return start <= now and now <= end


async def update_from_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if the update is from an admin either:
        - defined in the config json
        - chat admin in the Farthest chat on telegram
    """

    if update.effective_chat.id in ADMINS:
        return True

    if not update.effective_chat.id == FARTHER_CHAT_ID:
        return False

    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        if update.message.from_user.id in [admin.user.id for admin in admins]:
            return True
    except BadRequest:
        pass
    return False


async def usage_dispatcher(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''shortcut to making a usage message dispatcher'''
    return lambda: context.bot.send_message(chat_id=update.effective_chat.id,
                                            text=text,
                                            parse_mode="HTML",
                                            reply_to_message_id=update.effective_message.id)
