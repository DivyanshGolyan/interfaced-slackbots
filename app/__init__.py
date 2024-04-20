import os
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

from app.utils.logging import setup_logging, get_logger
from app.config import *
from app.slackbot.listeners import register_listeners
import asyncio

# db = SQLAlchemy()

import dotenv

load_dotenv()


async def create_app():
    flask_app = Flask(__name__)
    setup_logging()
    logger = get_logger(__name__)

    bolt_apps = await initialize_bolt_apps(SLACK_BOTS)
    await register_and_cleanup_bolt_apps(bolt_apps)
    await start_bolt_handlers(bolt_apps)

    logger.info("Application startup")
    return flask_app, bolt_apps


async def initialize_bolt_apps(slack_bots):
    bolt_apps = {}
    for bot_name, bot_config in slack_bots.items():
        bolt_app = AsyncApp(token=bot_config.get("bot_token"), name=bot_name)
        handler = AsyncSocketModeHandler(bolt_app, bot_config.get("app_token"))
        client = bolt_app.client
        bot_user_id = await get_bot_user_id(client)
        bolt_apps[bot_name] = {
            "bolt_app": bolt_app,
            "handler": handler,
            "client": client,
            "bot_user_id": bot_user_id,
        }
    return bolt_apps


async def register_and_cleanup_bolt_apps(bolt_apps):
    for bot_name, bot_info in bolt_apps.items():
        register_listeners(
            bot_info.get("bolt_app"),
            bot_name,
            bot_info.get("client"),
            bot_info.get("bot_user_id"),
        )
        await leave_unallowed_channels(bot_info.get("client"), bot_name)


async def start_bolt_handlers(bolt_apps, logger):
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
