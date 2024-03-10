# from flask import Flask

# from .db import db

# def create_app(config):
#     """
#     Create the base webapp
#     - load confing
#     - init the db
#     """
#     app = Flask('web_service')
#     app.config.from_object(config)
#     db.init_app(app)


# NOTE: flask routes that trigger messages to
# send in telegram should probably only do the last message
# could also just not lol

# shared code would be nice, but theres not too much to share tbh
# routes gotta respond with errors / updates rather than messages like telegram
# general logic will be the same but have differences everywhere lol

# NOTE: General thoughts on recieving updates from telegram on the webclient
# probably just be lazy and ping the webclient with a "reload" message
# telling it to reload the queue
#
# ig things like pause/play shld be pung from telegram as well