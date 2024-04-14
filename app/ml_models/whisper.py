import io
import os
import tempfile
from pydub import AudioSegment
from app.LLM_clients.openai_client import client as openai_client
import openai
from app.ml_models.model_wrappers import ModelWrapper
from app.config import WHISPER_MODEL, WHISPER_CHUNK_LIMIT, logger
import asyncio
from app.exceptions import *


class Whisper(ModelWrapper):
    async def call_model(self, file_type, file_bytes):
        format = file_type
        try:
            file = io.BytesIO(file_bytes)
            audio = AudioSegment.from_file(file, format=format)
        except Exception as e:
            logger.error(f"Error creating audio segment: {e}")
            raise AudioProcessingError(
                "Failed to process the audio file. Please ensure the file is not corrupted and is in a supported format."
            )

        try:
            file_size = len(file.getbuffer())
            audio_chunks = await self.split_audio_into_chunks(audio, file_size)
            transcription_result = await self.transcribe_audio_chunks(
                audio_chunks, format
            )
            del file_bytes
            del file
            return transcription_result
        except Exception as e:
            logger.error(f"An error occurred during audio processing: {e}")
            raise e

    async def split_audio_into_chunks(self, audio, file_size):
        """Split audio into manageable chunks."""
        try:
            chunk_limit = WHISPER_CHUNK_LIMIT
            duration_ms = int(audio.duration_seconds * 1000)
            chunk_size_ms = (
                int((chunk_limit / file_size) * duration_ms)
                if file_size > chunk_limit
                else duration_ms
            )
            return [
                audio[i : i + chunk_size_ms]
                for i in range(0, duration_ms, chunk_size_ms)
            ]
        except Exception as e:
            logger.error(f"Error splitting audio into chunks: {e}")
            raise AudioProcessingError(
                "Failed to split the audio into manageable chunks. Please ensure the audio file is not corrupted and try again."
            )

    async def transcribe_audio_chunks(self, audio_chunks, format):
        """Transcribe multiple audio chunks."""
        transcription_tasks = [
            self.transcribe_audio_chunk(chunk, format) for chunk in audio_chunks
        ]
        transcriptions = await asyncio.gather(*transcription_tasks)
        return " ".join(transcriptions)

    async def transcribe_audio_chunk(self, chunk, format):
        """Helper function to transcribe a single audio chunk."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{format}", delete=True
            ) as tmp_file:
                chunk.export(tmp_file.name, format=format)
                transcript = await self.transcribe_audio(tmp_file.name)
                return transcript
        except WhisperProcessingError as e:
            logger.error(
                f"Whisper processing error while transcribing audio chunk: {e}"
            )
            raise e
        except Exception as e:
            logger.error(f"General error transcribing audio chunk: {e}")
            raise e

    async def transcribe_audio(self, file_path):
        """Transcribe audio content from a file path."""
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await openai_client.audio.transcriptions.create(
                    model=WHISPER_MODEL, file=audio_file
                )
                return transcript.text
        except (
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.BadRequestError,
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.NotFoundError,
        ) as e:
            logger.error(f"{e.__class__.__name__} occurred: {e}")
            raise WhisperProcessingError(
                f"We encountered an issue while processing your audio file. Detailed error: {e}"
            )
