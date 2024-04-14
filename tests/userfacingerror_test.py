# import pytest
# from unittest.mock import AsyncMock, patch
# from app.slackbot.message_handler import process_message, handle_errors
# from app.exceptions import PDFProcessingError


# @pytest.mark.asyncio
# @patch("app.slackbot.message_handler.send_response")
# @patch("app.slackbot.message_handler.get_bot_user_id", return_value="U123456")
# @patch("app.slackbot.message_handler.fetch_thread_messages", return_value=AsyncMock())
# @patch(
#     "app.slackbot.message_handler.process_message",
#     side_effect=PDFProcessingError("Error processing PDF"),
# )
# async def test_error_propagation_from_deep_code(
#     mock_process_message,
#     mock_fetch_thread_messages,
#     mock_get_bot_user_id,
#     mock_send_response,
# ):
#     client = AsyncMock()
#     channel_id = "C12345"
#     thread_ts = "1234567890.123456"

#     # Simulate handling an event that triggers process_message
#     async with handle_errors(client, channel_id, thread_ts):
#         await process_message(
#             {"type": "message"}, "bot_name", client, channel_id, thread_ts
#         )

#     # Check if send_response was called with the error encapsulated in an AgentResponse
#     mock_send_response.assert_called_once()
#     args, kwargs = mock_send_response.call_args
#     assert kwargs["client"] == client
#     assert kwargs["channel_id"] == channel_id
#     assert kwargs["thread_ts"] == thread_ts
#     # assert isinstance(args[0], AgentResponse)
#     assert args[0].text == "Error processing PDF"
