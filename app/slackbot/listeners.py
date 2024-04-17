from app.slackbot.message_handler import *
from app.config import logger


def register_listeners(app, bot_name):
    logger.info(f"Registering listeners for {bot_name}")

    @app.event("app_mention")
    async def handle_app_mention(event, say, ack):
        await ack()
        slack_client = app.client
        channel_id = event.get("channel") or event.get("channel_id")
        thread_ts = event.get("thread_ts") or event.get("ts")
        async with handle_errors(slack_client, channel_id, thread_ts):
            await process_message(event, bot_name, slack_client, channel_id, thread_ts)

    @app.event("message")
    async def handle_direct_message(event, say, ack):
        await ack()
        if event.get("bot_id") is None:
            # await say("Received a message")
            slack_client = app.client
            channel_id = event.get("channel") or event.get("channel_id")
            thread_ts = event.get("thread_ts") or event.get("ts")
            async with handle_errors(slack_client, channel_id, thread_ts):
                await process_message(
                    event, bot_name, slack_client, channel_id, thread_ts
                )
