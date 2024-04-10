from app.slackbot.message_handler import process_message


def register_listeners(app, bot_name):
    @app.event("app_mention")
    async def handle_app_mention(event, say):
        await process_message(app, event, say, bot_name)

    @app.event("message")
    async def handle_direct_message(event, say):
        if event.get("bot_id") is None:
            await process_message(app, event, say, bot_name)
