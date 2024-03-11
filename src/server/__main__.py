import database
import streaming
import downloaders

if __name__ == "__main__":
    database.init()
    streaming.init()
    downloaders.init()

    # import this later cause of farther context needing
    # some things inited first
    import bot
    bot.launch()
