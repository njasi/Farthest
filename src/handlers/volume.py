from telegram import Update
from telegram.ext import ContextTypes
from handlers.helpers import usage_dispatcher

VOLUME_INCREMENT = 10
VOLUME_MAX = 100


async def volume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    handler to deal with the /volume (/v) command:

    /volume [level | -d | -u]
        - level must be an integer from 0-100
        - -d makes the volume go down by VOLUME_INCREMENT
        - -u makes the volume go up by VOLUME_INCREMENT
    '''
    current_volume = 100  # TODO link into the new queue
    usage = usage_dispatcher(
        "<b>Usage:</b>\n/volume [level | -d | -u]\n\tVolume must be an integer from 0-100\n\t-d makes the volume go down by a level\n\t -u makes the volume go up by a level", update, context)

    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"The current volume is {current_volume}%",
                                       parse_mode="HTML",
                                       reply_to_message_id=update.message.message_id)
        return
    if len(context.args) != 1:
        usage()
    try:
        value = int(context.args[0])
    except:
        if context.args[0] == "-d":
            value = current_volume - VOLUME_INCREMENT
        elif context.args[0] == "-u":
            value = current_volume + VOLUME_INCREMENT

        usage()

    # clamp to acceptable values
    if not value <= VOLUME_MAX:
        value = VOLUME_MAX
    if value < 0:
        value = 0

    # TODO set volume with new method
    # QUEUE.set_volume(value)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Volume set to {value}%",
                                   parse_mode="HTML",
                                   reply_to_message_id=update.message.message_id)
