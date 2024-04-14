import pytest
from unittest.mock import AsyncMock, patch
from app.ml_models.dalle import DALLE
from app.exceptions import DALLEProcessingError


@pytest.fixture
def dalle_instance():
    return DALLE()


@pytest.fixture
def sample_prompt():
    return "A futuristic cityscape at sunset"


@pytest.mark.asyncio
async def test_dalle_call_model_success(dalle_instance, sample_prompt):
    with patch(
        "app.ml_models.dalle.openai_client.images.generate",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = AsyncMock(
            data=[
                AsyncMock(
                    b64_json="base64_image_data",
                    revised_prompt="Revised: " + sample_prompt,
                )
            ]
        )
        revised_prompt, image_base64 = await dalle_instance.call_model(sample_prompt)
        assert revised_prompt == "Revised: " + sample_prompt
        assert image_base64 == "base64_image_data"


@pytest.mark.asyncio
async def test_dalle_call_model_prompt_too_long(dalle_instance):
    long_prompt = "A" * 5000  # Exceeds the 4000 character limit
    with pytest.raises(DALLEProcessingError) as exc_info:
        await dalle_instance.call_model(long_prompt)
    assert (
        "Prompt length exceeds the maximum allowed characters (4000 for dall-e-3)"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_dalle_call_model_rate_limit_error(dalle_instance, sample_prompt):
    with patch(
        "app.ml_models.dalle.openai_client.images.generate",
        side_effect=DALLEProcessingError(
            "Rate limit exceeded. Please wait before sending more requests."
        ),
    ):
        with pytest.raises(DALLEProcessingError) as exc_info:
            await dalle_instance.call_model(sample_prompt)
        assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dalle_call_model_internal_server_error(dalle_instance, sample_prompt):
    with patch(
        "app.ml_models.dalle.openai_client.images.generate",
        side_effect=DALLEProcessingError("Internal server error occurred."),
    ):
        with pytest.raises(DALLEProcessingError) as exc_info:
            await dalle_instance.call_model(sample_prompt)
        assert "Internal server error occurred" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dalle_call_model_actual_prompt(dalle_instance, sample_prompt):
    # Call the model with a sample prompt and capture the actual API response
    revised_prompt, image_base64 = await dalle_instance.call_model(sample_prompt)

    # Assertions to check if the returned data is as expected
    assert revised_prompt
    assert len(image_base64) > 0  # Check if some base64 image data is returned
