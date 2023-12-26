from telegram import Update
from telegram.ext import ContextTypes

from handlers.helpers import usage_dispatcher


def mute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Handler to deal with the mute command

    /mute - lowers the volume to 0
    '''
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/mute", update)

    if len(context.args) != 0:
        usage()
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Muted farther. Use /volume to give farther a voice again.",
                             parse_mode="HTML",
                             disable_web_page_preview=True,
                             reply_to_message_id=update.message.message_id)
    # TODO change out for new volume changing
    # QUEUE.set_volume(0)
