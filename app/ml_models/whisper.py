import io
import os
import tempfile
from pydub import AudioSegment
from LLM_clients.openai_client import client as openai_client
from config import logger
import openai
from model_wrappers import ModelWrapper
from app.config import WHISPER_MODEL, WHISPER_CHUNK_LIMIT
import asyncio


class Whisper(ModelWrapper):
    async def call_model(self, file_type, file_bytes):
        format = file_type
        if not format:
            raise ValueError("Unsupported MIME type")
        try:
            audio = AudioSegment.from_file(file_bytes, format=format)
            file_size = len(file_bytes.getbuffer())
            audio_chunks = await self.split_audio_into_chunks(audio, file_size)
            transcription_result = await self.transcribe_audio_chunks(
                audio_chunks, format
            )
            del file_bytes  # Delete the original file_bytes to free up memory
            return transcription_result
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e

    async def split_audio_into_chunks(self, audio, file_size):
        """Split audio into manageable chunks."""
        chunk_limit = WHISPER_CHUNK_LIMIT
        duration_ms = int(audio.duration_seconds * 1000)
        chunk_size_ms = (
            int((chunk_limit / file_size) * duration_ms)
            if file_size > chunk_limit
            else duration_ms
        )
        return [
            audio[i : i + chunk_size_ms] for i in range(0, duration_ms, chunk_size_ms)
        ]

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
                tmp_file.write(chunk.raw_data)
                tmp_file.flush()
                transcript = await self.transcribe_audio(tmp_file.name)
                return transcript
        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {e}")
            raise e

    async def transcribe_audio(self, file_path):
        """Transcribe audio content from a file path."""
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await openai_client.audio.transcribe(
                    model=WHISPER_MODEL, file=audio_file
                )
        except openai.APIConnectionError as e:
            logger.error("Connection error: The server could not be reached.")
            logger.error(f"Error details: {e}")
            raise e
        except openai.RateLimitError as e:
            logger.error(
                "Rate limit exceeded: A 429 status code was received; we should back off a bit."
            )
            raise e
        except openai.BadRequestError as e:
            logger.error("Bad request error: A 400 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e
        except openai.AuthenticationError as e:
            logger.error(
                "Authentication error: A 401 status code was received; Authentication failed."
            )
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e
        except openai.PermissionDeniedError as e:
            logger.error("Permission denied error: A 403 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e
        except openai.NotFoundError as e:
            logger.error("Not found error: A 404 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e
        return transcript["text"]
