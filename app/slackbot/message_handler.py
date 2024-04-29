from app.config import SLACK_BOTS, SLACK_THREAD_MESSAGE_LIMIT
from app.objects import SlackResponseHandler, SlackService
from contextlib import asynccontextmanager
from app.exceptions import *
from app.agents.agent_manager import AgentManager

from app.database.dao import create_message

agent_manager = AgentManager(SLACK_BOTS)


async def process_message(
    event, bot_name, slack_client, channel_id, thread_ts, bot_user_id
):
    bot_token = SLACK_BOTS.get(bot_name, {}).get("bot_token", "")
    agent = SLACK_BOTS.get(bot_name, {}).get("agent", "")
    event_type = event.get("type")
    user_message_ts = event.get("ts")
    if event_type == "app_mention":
        thread_ts = thread_ts or user_message_ts

    user = event.get("user")
    text = event.get("text")

    await create_message(
        channel_id=channel_id,
        thread_ts=thread_ts,
        sender_id=user,
        bot_name=bot_name,
        message_ts=user_message_ts,
        responding_to_ts=None,
        message_type=event_type,
        text=text,
    )

    thread_messages = await fetch_thread_messages(
        slack_client, channel_id, thread_ts, bot_token, bot_user_id, bot_name
    )
    agent = agent_manager.get_agent(bot_name)

    response_generator = agent.process_conversation(thread_messages)
    response_handler = SlackResponseHandler(
        client=slack_client,
        channel_id=channel_id,
        thread_ts=thread_ts,
        user_message_ts=user_message_ts,
        bot_name=bot_name,
        bot_user_id=bot_user_id,
    )
    await response_handler.handle_responses(response_generator=response_generator)


async def fetch_thread_messages(
    client, channel_id, thread_ts, bot_token, bot_user_id, bot_name
):
    all_thread_data = []
    try:
        cursor = None
        while True:
            response = await client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                cursor=cursor,
                limit=200,  # Recommended limit for batch processing
            )
            if response["ok"]:
                thread_data = response["messages"]
                all_thread_data.extend(thread_data)

                if len(all_thread_data) > SLACK_THREAD_MESSAGE_LIMIT:
                    raise UserFacingError(
                        f"This thread has grown too large for me to process. To avoid potential performance issues, I am limited to working with threads containing {SLACK_THREAD_MESSAGE_LIMIT} messages or less. Please try again with a shorter thread or feel free to start a new conversation."
                    )

                # Check for the presence of a "next_cursor" to continue pagination
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            else:
                raise Exception(f"Failed to fetch thread messages: {response['error']}")

        slack_service = SlackService(bot_name)
        conversation = await slack_service.create_conversation_from_thread(
            all_thread_data, bot_token, channel_id, thread_ts, bot_user_id
        )
        return conversation
    except Exception as e:
        raise Exception(f"Error fetching thread messages: {str(e)}")


@asynccontextmanager
async def handle_errors(client, channel_id, thread_ts):
    try:
        yield
    except UserFacingError as e:
        await client.chat_postMessage(
            text=e.message,
            channel=channel_id,
            thread_ts=thread_ts,
        )
