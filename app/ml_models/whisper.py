import io
import os
import tempfile
from pydub import AudioSegment
from LLM_clients.openai_client import client as openai_client
from config import logger
import openai
from model_wrappers import ModelWrapper
from app.config import WHISPER_MODEL


class Whisper(ModelWrapper):
    async def call_model(self, input_data):
        try:
            file_content = input_data.get("file_content")
            file_type = input_data.get("file_type")
            if len(file_content.getbuffer()) > 25 * 1024 * 1024:
                # logger.debug("Reading and splitting the audio into chunks...")
                audio = AudioSegment.from_file(file_content, file_type)
                audio_chunks = self.split_audio_into_chunks(
                    audio, len(file_content.getbuffer())
                )
                # logger.debug(f"Created {len(audio_chunks)} audio chunks.")

                # logger.debug("Transcribing audio chunks...")
                transcriptions = await self.transcribe_audio_chunks(
                    audio_chunks, file_type
                )
                # logger.debug("All chunks transcribed successfully.")

                transcription_result = " ".join(transcriptions)
                # logger.debug("Transcriptions joined successfully.")
                return transcription_result
            else:
                file_content.seek(0)
                # logger.debug("Transcribing the audio file...")
                transcript = await self.transcribe_audio(file_content, file_type)
                return [transcript]
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e

    def split_audio_into_chunks(self, audio, file_size):
        """Split audio into manageable chunks."""
        chunk_limit = 25 * 1024 * 1024  # 25MB
        chunk_size_ms = (chunk_limit / file_size) * audio.duration_seconds * 1000
        return [
            audio[i : i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)
        ]

    async def transcribe_audio_chunks(self, audio_chunks, file_type):
        """Transcribe multiple audio chunks."""
        transcriptions = []
        for idx, chunk in enumerate(audio_chunks):
            try:
                transcript = await self.transcribe_audio(
                    io.BytesIO(chunk.raw_data), file_type
                )
                transcriptions.append(transcript)
            except Exception as e:
                logger.error(f"Error transcribing chunk {idx}: {e}")
                raise e
        return transcriptions

    async def transcribe_audio(self, audio_content, file_type):
        """Transcribe audio content."""
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_type}", delete=False
        ) as tmp_file:
            if isinstance(audio_content, io.BytesIO):
                tmp_file.write(audio_content.getvalue())
            else:
                tmp_file.write(audio_content.read())
            tmp_file.flush()
            with open(tmp_file.name, "rb") as audio_file:
                try:
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
                    logger.error(
                        f"Status code: {e.status_code}, Response: {e.response}"
                    )
                    raise e
                except openai.AuthenticationError as e:
                    logger.error(
                        "Authentication error: A 401 status code was received; Authentication failed."
                    )
                    logger.error(
                        f"Status code: {e.status_code}, Response: {e.response}"
                    )
                    raise e
                except openai.PermissionDeniedError as e:
                    logger.error(
                        "Permission denied error: A 403 status code was received."
                    )
                    logger.error(
                        f"Status code: {e.status_code}, Response: {e.response}"
                    )
                    raise e
                except openai.NotFoundError as e:
                    logger.error("Not found error: A 404 status code was received.")
                    logger.error(
                        f"Status code: {e.status_code}, Response: {e.response}"
                    )
                    raise e
            os.remove(tmp_file.name)
        return transcript["text"]
