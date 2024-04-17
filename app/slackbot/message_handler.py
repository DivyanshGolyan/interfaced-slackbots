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
    user_message_ts = event.get("ts")
    if event_type == "app_mention":
        thread_ts = thread_ts or user_message_ts
    bot_user_id = await get_bot_user_id(slack_client)

    thread_messages = await fetch_thread_messages(
        slack_client, channel_id, thread_ts, bot_token, bot_user_id
    )
    agent = agent_manager.get_agent(bot_name)

    response_generator = agent.process_conversation(thread_messages)
    response_handler = SlackResponseHandler(
        client=slack_client, channel_id=channel_id, thread_ts=thread_ts
    )
    await response_handler.handle_responses(response_generator=response_generator)

    # await handle_agent_responses(
    #     slack_client,
    #     response_generator,
    #     channel_id,
    #     thread_ts,
    #     bot_user_id,
    #     user_message_ts,
    # )


# async def handle_agent_responses(
#     client, response_generator, channel_id, thread_ts, bot_user_id, user_message_ts
# ):
#     first_response = True
#     bot_message_ts = None
#     accumulated_text = ""
#     typing_indicator_text = f"\n\n:typing-bubble:"

#     async for agent_response in response_generator:
#         if not agent_response.end_of_stream:
#             agent_response.add_text(typing_indicator_text)

#         if first_response:
#             await send_response(client, agent_response, channel_id, thread_ts)
#             first_response = False
#             accumulated_text += agent_response.text
#             bot_message_ts = await fetch_first_bot_message_ts_after_event(
#                 client, channel_id, thread_ts, bot_user_id, user_message_ts
#             )
#         else:
#             if bot_message_ts:
#                 try:
#                     accumulated_text = accumulated_text.replace(
#                         typing_indicator_text, ""
#                     )
#                     new_accumulated_text = accumulated_text + agent_response.text
#                     if len(new_accumulated_text) > 3900:
#                         # If accumulated_text exceeds 3900 characters, send a new message and reset accumulated_text
#                         await update_message_text(
#                             client,
#                             channel_id,
#                             bot_message_ts,
#                             AgentResponse(accumulated_text),
#                         )
#                         bot_message_ts = await send_response(
#                             client,
#                             AgentResponse(agent_response.text),
#                             channel_id,
#                             thread_ts,
#                         )
#                         accumulated_text = agent_response.text
#                     else:
#                         await update_message_text(
#                             client,
#                             channel_id,
#                             bot_message_ts,
#                             AgentResponse(new_accumulated_text),
#                         )
#                         accumulated_text = new_accumulated_text
#                 except Exception as e:
#                     # If updating fails, send a new message and reset accumulated_text
#                     bot_message_ts = await send_response(
#                         client,
#                         AgentResponse(agent_response.text),
#                         channel_id,
#                         thread_ts,
#                     )
#                     accumulated_text = agent_response.text
#             else:
#                 raise Exception(
#                     "Failed to fetch bot message timestamp for updating message"
#                 )


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


# async def fetch_first_bot_message_ts_after_event(
#     client, channel_id, thread_ts, bot_user_id, user_message_ts
# ):
#     cursor = None
#     try:
#         while True:
#             response = await client.conversations_replies(
#                 channel=channel_id,
#                 ts=thread_ts,
#                 cursor=cursor,
#                 limit=200,  # Recommended limit for batch processing
#             )
#             if response["ok"]:
#                 messages = response["messages"]
#                 # Filter messages to find the first bot message after the specified user message timestamp
#                 for message in messages:
#                     if message.get("user") == bot_user_id and float(
#                         message.get("ts")
#                     ) > float(user_message_ts):
#                         return message.get(
#                             "ts"
#                         )  # Return the timestamp of the first bot message after the user message ts
#                 # Check for the presence of a "next_cursor" to continue pagination
#                 cursor = response.get("response_metadata", {}).get("next_cursor")
#                 if not cursor:
#                     break
#             else:
#                 raise Exception(f"Failed to fetch messages: {response['error']}")
#     except Exception as e:
#         raise Exception(
#             f"Error fetching first bot message timestamp after {user_message_ts}: {str(e)}"
#         )
#     return None  # Return None if no suitable bot message is found


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
        await client.chat_postMessage(
            text=e.message,
            channel=channel_id,
            thread_ts=thread_ts,
        )


# async def send_response(client, agent_response, channel_id, thread_ts):
#     if agent_response.files:
#         file_uploads = []
#         for file in agent_response.files:
#             file_uploads.append(
#                 {
#                     "content": file.file_bytes,
#                     "title": (file.title if file.title else None),
#                 }
#             )
#         initial_comment = agent_response.text if agent_response.text else None
#         response = await client.files_upload_v2(
#             file_uploads=file_uploads,
#             channel=channel_id,
#             initial_comment=initial_comment,
#             thread_ts=thread_ts,
#         )
#         return (
#             response.get("file", {})
#             .get("shares", {})
#             .get("public", {})
#             .get(channel_id, [{}])[0]
#             .get("ts")
#         )
#     elif agent_response.text:
#         response = await client.chat_postMessage(
#             channel=channel_id, text=agent_response.text, thread_ts=thread_ts
#         )
#         return response.get("ts")


# async def update_message_text(client, channel_id, bot_message_ts, agent_response):
#     await client.chat_update(
#         channel=channel_id, ts=bot_message_ts, text=agent_response.text
#     )
