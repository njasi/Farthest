# start the database
import database
# import the bot
import bot.main as bot
# TODO import flask once it's made

if __name__ == "__main__":
    database.init()
    bot.start()
