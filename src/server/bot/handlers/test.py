from telegram import Update
from telegram.ext import ContextTypes

from bot.FartherContext import FartherContext

from database import History, Video

def test_callback(update: Update, context: FartherContext):
    '''
    handler for testing things
    '''



