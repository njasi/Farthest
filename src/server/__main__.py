# start the database
import database
import bot.main as bot


if __name__ == "__main__":
    database.init()
    bot.start()
