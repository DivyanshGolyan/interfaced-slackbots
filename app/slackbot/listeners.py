from app.slackbot.message_handler import process_message


def register_listeners(app):
    @app.event("app_mention")
    def handle_app_mention(event, say):
        process_message(event, say)

    @app.event("message")
    def handle_direct_message(event, say):
        # Ignore messages from the bot itself
        if event.get("bot_id") is None:
            process_message(event, say)

    @app.middleware
    def log_request(logger, body, next):
        # Log incoming requests for the specific bot
        logger.debug(body)
        return next()
