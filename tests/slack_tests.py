import pytest
from unittest.mock import AsyncMock, patch
from app.objects import *
from app.slackbot.message_handler import *
from app.agents.agent_manager import AgentManager
from app.config import SLACK_BOTS
from app.slackbot.listeners import register_listeners

agent_manager = AgentManager(SLACK_BOTS)


@pytest.mark.asyncio
async def test_process_message_success():
    mock_agent = AsyncMock()
    mock_agent.process_conversation = AsyncMock(
        return_value=AgentResponse(text="Test response")
    )

    with patch(
        "app.slackbot.message_handler.AgentManager.get_agent", return_value=mock_agent
    ), patch(
        "app.slackbot.message_handler.fetch_thread_messages",
        AsyncMock(return_value="Mocked Conversation"),
    ), patch(
        "app.slackbot.message_handler.send_response", AsyncMock()
    ) as mock_send:

        await process_message(
            {"type": "message"}, "bot_name", AsyncMock(), "channel_id", "thread_ts"
        )
        mock_send.assert_called()


# @pytest.mark.asyncio
# async def test_process_message_success():
#     with patch(
#         "app.slackbot.message_handler.fetch_thread_messages",
#         AsyncMock(return_value="Mocked Conversation"),
#     ), patch("app.slackbot.message_handler.send_response", AsyncMock()) as mock_send:
#         await process_message(
#             {"type": "message"}, "bot_name", AsyncMock(), "channel_id", "thread_ts"
#         )
#         mock_send.assert_called()


@pytest.mark.asyncio
async def test_process_message_failure():
    with patch(
        "app.slackbot.message_handler.fetch_thread_messages",
        AsyncMock(side_effect=Exception("Error")),
    ), patch("app.slackbot.message_handler.send_response", AsyncMock()) as mock_send:
        with pytest.raises(Exception):
            await process_message(
                {"type": "message"}, "bot_name", AsyncMock(), "channel_id", "thread_ts"
            )
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_response_with_text():
    client_mock = AsyncMock()
    await send_response(
        client_mock, AgentResponse(text="Hello"), "channel_id", "thread_ts"
    )
    client_mock.chat_postMessage.assert_called_with(
        channel="channel_id", text="Hello", thread_ts="thread_ts"
    )


@pytest.mark.asyncio
async def test_send_response_with_files():
    client_mock = AsyncMock()
    agent_response = AgentResponse()
    agent_response_file = AgentResponseFile(file_bytes=b"Sample")
    agent_response.add_file(agent_response_file)
    await send_response(client_mock, agent_response, "channel_id", "thread_ts")
    client_mock.files_upload_v2.assert_called()


async def test_register_listeners():
    app_mock = AsyncMock()
    await register_listeners(app_mock, "bot_name")
    app_mock.event.assert_any_call("app_mention")
    app_mock.event.assert_any_call("message")
