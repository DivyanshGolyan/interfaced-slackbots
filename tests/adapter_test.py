import pytest
from unittest.mock import AsyncMock, patch
from app.adapters.gpt_adapter import GPTAdapter
from app.objects import *


@pytest.mark.asyncio
async def test_convert_conversation():
    # Setup
    adapter = GPTAdapter()
    conversation = TransformedSlackConversation()
    message1 = TransformedSlackMessage(user_id="U123", bot_user_id="U123")
    message1.add_text("Hello, how are you?")
    message2 = TransformedSlackMessage(user_id="U456", bot_user_id="U123")
    message2.add_text("What's the weather today?")
    conversation.add_message(message1)
    conversation.add_message(message2)

    with patch.object(
        adapter, "convert_message", new_callable=AsyncMock
    ) as mock_convert_message:
        mock_convert_message.side_effect = [
            {
                "role": "assistant",
                "name": "U123",
                "content": [{"type": "text", "text": "Hello, how are you?"}],
            },
            {
                "role": "user",
                "name": "U456",
                "content": [{"type": "text", "text": "What's the weather today?"}],
            },
        ]

        # Execute
        result = await adapter.convert_conversation(conversation)

        # Verify
        assert len(result) == 3  # System message + 2 converted messages
        assert result[0]["role"] == "system"
        assert (
            "You are an autoregressive language model" in result[0]["content"]["text"]
        )
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "user"


@pytest.mark.asyncio
async def test_convert_message_with_text():
    # Setup
    adapter = GPTAdapter()
    message = TransformedSlackMessage(user_id="U123", bot_user_id="U123")
    message.add_text("Sample text")

    # Execute
    result = await adapter.convert_message(message)

    # Verify
    assert result["role"] == "assistant"
    assert result["name"] == "U123"
    assert result["content"][0]["type"] == "text"
    assert result["content"][0]["text"] == "Sample text"


@pytest.mark.asyncio
async def test_convert_message_with_files():
    # Setup
    adapter = GPTAdapter()
    file_content = b"fake_image_data"
    message = TransformedSlackMessage(user_id="U123", bot_user_id="U123")
    message.add_text("Check this out")
    processed_file = ProcessedFile(file_type="png", file_bytes=file_content)
    message.add_file(processed_file)

    with patch(
        "app.utils.file_utils.image_bytes_to_base64", new_callable=AsyncMock
    ) as mock_base64:
        mock_base64.return_value = "ZmFrZV9pbWFnZV9kYXRh"

        # Execute
        result = await adapter.convert_message(message)

        # Verify
        assert result["role"] == "assistant"
        assert result["name"] == "U123"
        assert result["content"][1]["type"] == "image_url"
        assert (
            result["content"][1]["image_url"]["url"]
            == "data:image/png;base64,ZmFrZV9pbWFnZV9kYXRh"
        )
