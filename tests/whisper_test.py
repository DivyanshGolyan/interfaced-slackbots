import pytest
from unittest.mock import AsyncMock, patch
from app.ml_models.whisper import Whisper
from app.exceptions import AudioProcessingError, WhisperProcessingError
from openai.types.audio.transcription import Transcription


@pytest.fixture
def whisper_instance():
    return Whisper()


@pytest.fixture
def sample_audio_bytes():
    with open("tests/test_files/sample_speech.mp3", "rb") as f:
        return f.read()


@pytest.mark.asyncio
async def test_whisper_call_model_success(whisper_instance, sample_audio_bytes):
    with patch(
        "app.ml_models.whisper.openai_client.audio.transcriptions.create",
        new_callable=AsyncMock,
    ) as mock_transcribe:
        mock_transcribe.return_value = Transcription(
            text="This is a test transcription."
        )
        result = await whisper_instance.call_model("mp3", sample_audio_bytes)
        assert result == "This is a test transcription."


@pytest.mark.asyncio
async def test_whisper_call_model_audio_processing_error(
    whisper_instance, sample_audio_bytes
):
    with patch(
        "app.ml_models.whisper.AudioSegment.from_file",
        side_effect=Exception("Audio processing failed"),
    ):
        with pytest.raises(AudioProcessingError):
            await whisper_instance.call_model("mp3", sample_audio_bytes)


@pytest.mark.asyncio
async def test_whisper_call_model_transcription_error(
    whisper_instance, sample_audio_bytes
):
    with patch(
        "app.ml_models.whisper.openai_client.audio.transcriptions.create",
        side_effect=WhisperProcessingError("Transcription failed"),
    ):
        with pytest.raises(WhisperProcessingError):
            await whisper_instance.call_model("mp3", sample_audio_bytes)


@pytest.mark.asyncio
async def test_whisper_integration_with_real_file(whisper_instance):
    with open("tests/test_files/sample_speech.mp3", "rb") as file:
        file_bytes = file.read()
        print(f"Size of file in bytes: {len(file_bytes)}")
    result = await whisper_instance.call_model("mp3", file_bytes)
    assert isinstance(result, str)
