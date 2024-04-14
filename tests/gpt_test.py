import pytest
from unittest.mock import AsyncMock, patch
from app.ml_models.gpt import GPT
from app.exceptions import GPTProcessingError


@pytest.fixture
def gpt_instance():
    return GPT()


@pytest.fixture
def sample_input_data():
    return [{"role": "user", "content": "What is the weather like today?"}]


@pytest.mark.asyncio
async def test_gpt_call_model_success(gpt_instance, sample_input_data):
    with patch(
        "app.ml_models.gpt.openai_client.chat.completions.create",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = AsyncMock(
            choices=[
                AsyncMock(
                    finish_reason="completed",
                    message=AsyncMock(content="Sunny and clear"),
                )
            ],
            usage=AsyncMock(prompt_tokens=10, completion_tokens=5),
        )
        message_content, prompt_tokens, completion_tokens = (
            await gpt_instance.call_model(sample_input_data)
        )
        assert message_content == "Sunny and clear"
        assert prompt_tokens == 10
        assert completion_tokens == 5


@pytest.mark.asyncio
async def test_gpt_call_model_rate_limit_error(gpt_instance, sample_input_data):
    with patch(
        "app.ml_models.gpt.openai_client.chat.completions.create",
        side_effect=GPTProcessingError(
            "Rate limit exceeded. Please wait before sending more requests."
        ),
    ):
        with pytest.raises(GPTProcessingError) as exc_info:
            await gpt_instance.call_model(sample_input_data)
        assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gpt_call_model_bad_request_error(gpt_instance, sample_input_data):
    with patch(
        "app.ml_models.gpt.openai_client.chat.completions.create",
        side_effect=GPTProcessingError(
            "The conversation is too long. Please reduce the length and try again."
        ),
    ):
        with pytest.raises(GPTProcessingError) as exc_info:
            await gpt_instance.call_model(sample_input_data)
        assert "The conversation is too long" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gpt_call_model_internal_server_error(gpt_instance, sample_input_data):
    with patch(
        "app.ml_models.gpt.openai_client.chat.completions.create",
        side_effect=GPTProcessingError("Internal server error occurred."),
    ):
        with pytest.raises(GPTProcessingError) as exc_info:
            await gpt_instance.call_model(sample_input_data)
        assert "Internal server error occurred" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gpt_actual_api_call(gpt_instance):
    sample_text = [{"role": "user", "content": "Tell me a joke."}]
    response = await gpt_instance.call_model(sample_text)
    assert isinstance(response, tuple)
    assert (
        len(response) == 3
    )  # Expecting a tuple of (message_content, prompt_tokens, completion_tokens)
