import database
import streaming

if __name__ == "__main__":
    database.init()
    streaming.init()

    # import this later cause of farther context needing
    # some things inited first
    import bot.main as bot
    bot.launch()
