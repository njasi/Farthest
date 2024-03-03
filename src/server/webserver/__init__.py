from flask import Flask

from .db import db

def create_app(config):
    """
    Create the base webapp
    - load confing
    - init the db 
    """
    app = Flask('web_service')
    app.config.from_object(config)
    db.init_app(app)

