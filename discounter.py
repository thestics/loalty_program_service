import os
from logging.handlers import WatchedFileHandler

from flask import Flask

from config import LOG_TO, LOGGER, BaseConfig

if not os.path.exists(LOG_TO):
    os.makedirs(LOG_TO)

from models import db
from utils import Logger


fh = WatchedFileHandler(os.path.join(LOG_TO, LOGGER['file']))
fh.setLevel(LOGGER['level'])
fh.setFormatter(LOGGER['formatter'])

log = Logger(fh, "erc-py")


def create_app(config=None):
    app = Flask(BaseConfig.PROJECT, instance_relative_config=True)
    log.info("Service started!")

    configure_app(app, config)

    return app


def configure_app(app, config=None):
    app.config.from_object(config or BaseConfig)

    from views import blueprint
    app.register_blueprint(blueprint)

    @app.before_request
    def _db_connect():
        if db.is_closed():
            db.connect()

    @app.teardown_request
    def _db_close(exc):
        if not db.is_closed():
            db.close()
