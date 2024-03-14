import logging
import database
import streaming
import downloaders

# load in env file, u may want to change `override`
# I just have it cause vscode is being annoying
from dotenv import load_dotenv

load_dotenv(override=True)


# Define the logging format with dynamic indentation
def dynamic_indentation(record):
    indentation = " " * (20 - len(record.name))  # Adjust the number 20 as needed
    return f"%(asctime)s - [%(name)s] - %(levelname)s -{indentation} %(message)s"


# basic logging setup
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s - [%(name)s] - %(levelname)s - %(message)s")

if __name__ == "__main__":
    database.init()
    streaming.init()
    downloaders.init()

    # import this later cause of farther context needing
    # some things inited first
    import bot

    bot.launch()
