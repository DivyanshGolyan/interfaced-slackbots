# from app.database.dao import create_conversation, get_conversation, create_message
from app.config import SLACK_BOTS
from app.objects import *
from contextlib import asynccontextmanager
from app.exceptions import *
from app.agents.agent_manager import AgentManager

agent_manager = AgentManager(SLACK_BOTS)


async def process_message(event, bot_name, slack_client, channel_id, thread_ts):
    bot_token = SLACK_BOTS.get(bot_name, {}).get("bot_token", "")
    agent = SLACK_BOTS.get(bot_name, {}).get("agent", "")
    event_type = event.get("type")
    if event_type == "app_mention":
        thread_ts = thread_ts or event.get("item", {}).get("ts")
    bot_user_id = await get_bot_user_id(slack_client)

    thread_messages = await fetch_thread_messages(
        slack_client, channel_id, thread_ts, bot_token, bot_user_id
    )
    agent = agent_manager.get_agent(bot_name)

    agent_response = await agent.process_conversation(thread_messages)

    if isinstance(agent_response, AgentResponse):
        await send_response(slack_client, agent_response, channel_id, thread_ts)
    else:
        raise TypeError("agent_response must be a AgentResponse object")

    # # Get or create the conversation
    # conversation = await get_or_create_conversation(channel_id, thread_ts, user_id)

    # # Save the user's message and the bot's response to the database
    # await save_message(conversation.id, user_id, inputs, response)

    # await process_response(response, channel_id, thread_ts, say, is_stream=True)


async def fetch_thread_messages(client, channel_id, thread_ts, bot_token, bot_user_id):
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
                # Check for the presence of a "next_cursor" to continue pagination
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            else:
                raise Exception(f"Failed to fetch thread messages: {response['error']}")
        conversation = slack_conversation(
            all_thread_data, bot_token, channel_id, thread_ts, bot_user_id
        )
        return conversation
    except Exception as e:
        raise Exception(f"Error fetching thread messages: {str(e)}")


async def get_bot_user_id(client):
    try:
        response = await client.auth_test()
        if response["ok"]:
            return response.get("user_id")
    except Exception as e:
        return None, str(e)


@asynccontextmanager
async def handle_errors(client, channel_id, thread_ts):
    try:
        yield
    except UserFacingError as e:
        await send_response(client, AgentResponse(e), channel_id, thread_ts)


# async def get_or_create_conversation(channel_id, thread_ts, user_id):
#     conversation = await get_conversation(channel_id, thread_ts)
#     if not conversation:
#         conversation = await create_conversation(user_id, channel_id, thread_ts)
#     return conversation


# async def save_message(conversation_id, user_id, inputs, response):
#     # Save user's message
#     await create_message(conversation_id, user_id, str(inputs))
#     # Save bot's response (text portion)
#     if "text" in response:
#         await create_message(conversation_id, "bot", response["text"])


async def send_response(client, agent_response, channel_id, thread_ts):
    if agent_response.files:
        file_uploads = []
        for file in agent_response.files:
            file_uploads.append(
                {
                    "content": file.file_bytes,
                    "title": (file.title if file.title else None),
                }
            )
        initial_comment = agent_response.text if agent_response.text else None
        await client.files_upload_v2(
            file_uploads=file_uploads,
            channel=channel_id,
            initial_comment=initial_comment,
            thread_ts=thread_ts,
        )
    elif agent_response.text:
        await client.chat_postMessage(
            channel=channel_id, text=agent_response.text, thread_ts=thread_ts
        )


# async def process_response(response, channel_id, thread_ts, say, is_stream=False):
#     if is_stream:
#         await handle_streamed_response(response, channel_id, thread_ts, say)
#     else:
#         await send_response(response, channel_id, thread_ts, say)


# async def handle_streamed_response(stream, channel_id, thread_ts, say, batch_by="."):
#     """
#     Handles the streamed response, batching it based on the specified character (default is period for sentences),
#     and sends the batched response to the user.
#     """
#     batched_text = ""
#     for chunk in stream:
#         if chunk.choices[0].delta.content is not None:
#             content = chunk.choices[0].delta.content
#             batched_text += content
#             # Batch by the specified character (e.g., end of a sentence)
#             if content.endswith(batch_by):
#                 await send_response({"text": batched_text}, channel_id, thread_ts, say)
#                 batched_text = ""
#     # Send any remaining text that didn't end with the batch character
#     if batched_text:
#         await send_response({"text": batched_text}, channel_id, thread_ts, say)
