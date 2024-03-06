# start the database
import database
# import the bot
import bot.main as bot
import streaming
# TODO import flask once it's made

if __name__ == "__main__":
    database.init()
    streaming.init()
    bot.launch()
