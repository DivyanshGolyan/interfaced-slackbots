from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from flask import Flask

from app.utils.logging import setup_logging, get_logger
from app.config import *
import asyncio

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import AsyncEngine

# from app.database.models import *

db = SQLAlchemy()
async_session = None


async def setup_database(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+asyncmy://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    global async_session
    async_engine = create_async_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
    async_session = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    # Create tables if needed
    await create_tables(async_engine)


async def create_tables(engine: AsyncEngine):
    from app.database.models import Conversation, Message, File

    try:
        async with engine.begin() as conn:
            await conn.run_sync(db.metadata.create_all)
        print("All tables created.")
    except Exception as e:
        print(f"Error creating tables: {e}")


async def create_app():
    flask_app = Flask(__name__)
    setup_logging()
    logger = get_logger(__name__)

    await setup_database(flask_app)

    bolt_apps = await initialize_bolt_apps(SLACK_BOTS)
    await register_and_cleanup_bolt_apps(bolt_apps)
    await start_bolt_handlers(bolt_apps)

    logger.info("Application startup")
    return flask_app, bolt_apps


async def initialize_bolt_apps(slack_bots):
    # from app.database.dao import create_bot

    bolt_apps = {}
    for bot_name, bot_config in slack_bots.items():
        bolt_app = AsyncApp(token=bot_config.get("bot_token"), name=bot_name)
        handler = AsyncSocketModeHandler(bolt_app, bot_config.get("app_token"))
        client = bolt_app.client
        bot_user_id = await get_bot_user_id(client)

        # await create_bot(bot_name)

        bolt_apps[bot_name] = {
            "bolt_app": bolt_app,
            "handler": handler,
            "client": client,
            "bot_user_id": bot_user_id,
        }
    return bolt_apps


async def register_and_cleanup_bolt_apps(bolt_apps):
    from app.slackbot.listeners import register_listeners

    for bot_name, bot_info in bolt_apps.items():
        bolt_app = bot_info.get("bolt_app")
        bolt_client = bot_info.get("client")
        bot_user_id = bot_info.get("bot_user_id")
        register_listeners(
            bolt_app,
            bot_name,
            bolt_client,
            bot_user_id,
        )
        await leave_unallowed_channels(bolt_client, bot_name)
        await send_wake_up_message(bolt_client)


async def start_bolt_handlers(bolt_apps):
    handlers = [
        bot_info.get("handler").start_async() for bot_info in bolt_apps.values()
    ]
    await asyncio.gather(*handlers)
    logger.info("All handlers started")


async def get_bot_user_id(client):
    response = await client.auth_test()
    if response["ok"]:
        return response.get("user_id")


async def leave_unallowed_channels(client, bot_name):
    cursor = None
    while True:
        response = await client.conversations_list(
            cursor=cursor, types="public_channel,private_channel"
        )
        if not response["ok"]:
            break

        channels = response.get("channels", [])
        for channel in channels:
            channel_id = channel.get("id")
            bot_is_member = channel.get("is_member")
            if bot_is_member and channel_id not in LIST_OF_ALLOWED_CHANNELS:
                await client.conversations_leave(channel=channel_id)
                logger.info(f"{bot_name} left channel {channel_id}")

        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break


async def send_wake_up_message(client):
    await client.chat_postMessage(
        channel=MAINTAINER_SLACK_USER_ID, text="I've just been restarted."
    )
