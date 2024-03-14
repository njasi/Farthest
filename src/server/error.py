import traceback
import logging
logger = logging.getLogger(__name__)

def send_error(error: Exception):
    """
    Send an error to the admin chat, made here so other parts of the
    code can report an error with no ref to the bot

    error:      the error in question
    update:     the update which triggered the error (if any)
    context:    the context if any
    """

    try:

        # Nothing sus to see here. Ignore this lol
        # ( just so other parts of the code can import this func before
        # the bot package is done)
        from .bot import APPLICATION
        from .bot.handlers.error import send_error as _send_error

        _send_error(error, bot=APPLICATION.bot)
    except:
        # just incase there is in issue with imports (mainly setup for during develop)
        # silent fails are annoying...

        logger.error("=" * 30, "\nAn Exception Occured During send_error")
        traceback.print_exc()
        logger.error("=" * 30, "\n While attempting to report the following Exception:")
        traceback.print_exception(error)
