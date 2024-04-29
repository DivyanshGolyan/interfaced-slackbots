from app.slackbot.message_handler import handle_errors, process_message
from app.config import *

processed_events_cache = set()


def register_listeners(app, bot_name, client, bot_user_id):
    logger.info(f"Registering listeners for {bot_name}")

    @app.event("app_mention")
    async def handle_app_mention(event, say, ack):
        await ack()
        if (event.get("ts"), bot_name) in processed_events_cache:
            logger.info("Duplicate event detected, skipping...")
            return
        processed_events_cache.add((event.get("ts"), bot_name))
        channel_id = event.get("channel") or event.get("channel_id")
        thread_ts = event.get("thread_ts") or event.get("ts")
        async with handle_errors(client, channel_id, thread_ts):
            await process_message(
                event, bot_name, client, channel_id, thread_ts, bot_user_id
            )

    @app.event("message")
    async def handle_direct_message(event, say, ack):
        await ack()
        if event.get("bot_id") is None:
            if (event.get("ts"), bot_name) in processed_events_cache:
                logger.info("Duplicate event detected, skipping...")
                return
            processed_events_cache.add((event.get("ts"), bot_name))
            channel_id = event.get("channel") or event.get("channel_id")
            thread_ts = event.get("thread_ts") or event.get("ts")
            async with handle_errors(client, channel_id, thread_ts):
                await process_message(
                    event, bot_name, client, channel_id, thread_ts, bot_user_id
                )

    @app.event("member_joined_channel")
    async def handle_member_joined_channel_events(event):
        added_user = event.get("user")
        channel = event.get("channel")
        inviting_user = event.get("inviter")
        if added_user == bot_user_id and channel not in LIST_OF_ALLOWED_CHANNELS:
            await client.conversations_leave(channel=channel)
            await client.chat_postMessage(
                channel=inviting_user,
                text=f"You invited me to join <#{channel}>. Unfortunately, our security policies do not allow me to join any channels apart from {', '.join(f'<#{ch}>' for ch in LIST_OF_ALLOWED_CHANNELS)}.\nYou can always DM me directly.\n\nIf you really want me to join <#{channel}>, please get an infosec approval and then, reach out to Divyansh.",
            )
