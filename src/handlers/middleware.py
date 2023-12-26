'''
Middleware function generators to control access / control flow for handlers
'''

from telegram import Update
from telegram.ext import ContextTypes
from handlers.helpers import is_quiet_hour, update_from_admin


def is_admin(handler):
    """
    Function generator as it doesnt look like the telegram bot api supports
    middleware of any kind. Kinda weird tbh.
    """
    async def is_admin_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update_from_admin(update, context):
            return await handler(update, context)
        else:
            await update.effective_message.reply_html("Only an admin can do this.",
                                                      reply_to_message_id=update.effective_chat.id)
    return is_admin_middleware


def is_quiet(handler):
    '''
    Wrapper that only executes the handler if it is not quiet hours
    '''
    async def is_quiet_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_quiet_hour():
            await update.effective_message.reply_html(
                "<b>You cannot preform this action, as it is currently quiet hours:</b>\n"
                '''Quiet hours:
    - start after midnight sun-thur
    - start after 2am on fri-sat, sat-sun interfaces
    - end at 7am (as far as the bot is concerned)'''
            )
        else:
            return await handler(update, context)
    return is_quiet_middleware


def is_chat(handler, handler_wrong, chat_id: int):
    '''
    Will only preform the handler in the chat specified by <chat_id>
    '''
    async def is_chat_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id == chat_id:
            return await handler(update, context)
        else:
            return await handler_wrong(update, context)
    return is_chat_middleware
