import os
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode import SocketModeHandler
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from app.utils.logging import setup_logging, get_logger
from app.config import (
    SLACK_BOTS,
    CACHE_TYPE,
    CACHE_DEFAULT_TIMEOUT,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DB,
)
from app.slackbot.listeners import register_listeners
from app.agents.agent_manager import AgentManager

global_agent_manager = None


db = SQLAlchemy()


def create_app():
    global global_agent_manager
    global_agent_manager = AgentManager(SLACK_BOTS)

    flask_app = Flask(__name__)

    # Configure MySQL database
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(flask_app)

    # Create database tables if not exists (development environment)
    if os.environ.get("FLASK_ENV") == "development":
        with flask_app.app_context():
            db.create_all()

    # Initialize Slack Bolt apps for each bot using Socket Mode
    bolt_apps = {}
    for bot_name, bot_config in SLACK_BOTS.items():
        bolt_app = AsyncApp(token=bot_config["bot_token"], name=bot_name)
        handler = SocketModeHandler(bolt_app, bot_config["app_token"])
        bolt_apps[bot_name] = (bolt_app, handler)

    # Register event listeners and middleware for each bot
    for bot_name, (bolt_app, _) in bolt_apps.items():
        register_listeners(bolt_app, bot_name)

    # Start the Socket Mode handlers for each bot
    for _, (_, handler) in bolt_apps.items():
        handler.start()

    # Set up logging
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application startup")

    return flask_app, bolt_apps
