import database
import streaming
import downloaders

# load in env file, u may want to change `override`
# I just have it cause vscode is being annoying
from dotenv import load_dotenv

load_dotenv(override=True)

if __name__ == "__main__":
    database.init()
    streaming.init()
    downloaders.init()

    # import this later cause of farther context needing
    # some things inited first
    import bot

    bot.launch()
