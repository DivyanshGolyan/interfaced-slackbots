from agent_manager import Agent
from app.ml_models.gpt import GPT
from app.ml_models.whisper import Whisper
from app.utils.file_utils import (
    pdf_to_images,
    convert_image_to_png,
    convert_audio_to_mp3,
)
from app.objects import *
from contextlib import closing
import pypdf
import pypdf.errors
from app.config import logger
from app.adapters.gpt_adapter import GPTAdapter
import asyncio


class ChatGPT(Agent):
    def __init__(self):
        self.supported_mime_categories = [
            "text/",
            "image/",
            "application/pdf",
            "audio/",
        ]
        self.supported_image_types = [
            "png",
            "jpeg",
            "jpg",
            "webp",
            "gif",
        ]
        self.supported_audio_types = [
            "mp3",
            "wav",
            "webm",
        ]
        self.transcription_model = Whisper()
        self.model_adapter = GPTAdapter()
        self.end_model = GPT()

    async def process_conversation(self, conversation):
        if not isinstance(conversation, slack_conversation):
            raise TypeError("conversation is not a slack_conversation object")

        transformed_conversation = TransformedSlackConversation()

        transformed_messages = await asyncio.gather(
            *(self.process_message(message) for message in conversation.messages)
        )

        for transformed_message in transformed_messages:
            transformed_conversation.add_message(transformed_message)

        payload = await self.model_adapter.convert_conversation(
            transformed_conversation
        )

        text_response, prompt_tokens, completion_tokens = self.end_model.call_model(
            payload
        )

        agent_response = AgentResponse()
        agent_response.add_text(text_response)
        agent_response.add_metadata("prompt_tokens", prompt_tokens)
        agent_response.add_metadata("completion_tokens", completion_tokens)

        return agent_response

    async def process_message(self, message):
        if not isinstance(message, slack_message):
            raise TypeError("message is not a slack_message object")

        transformed_message = TransformedSlackMessage(
            message.user_id, message.bot_user_id
        )
        transformed_message.add_text(message.text)

        for file in message.files:
            await self.process_file(file, message, transformed_message)

        return transformed_message

    async def process_file(self, file, message, transformed_message):
        if not isinstance(transformed_message, TransformedSlackMessage):
            raise TypeError(
                "transformed_message is not a TransformedSlackMessage object"
            )

        mime_type = file.mimetype
        file_type = file.filetype
        mode = file.mode
        file_name = file.name

        if any(
            mime_type.startswith(category)
            for category in self.supported_mime_categories
        ) or mode in ["snippet", "post"]:
            file_bytes = await message.get_file_content(file)
            if not isinstance(file_bytes, bytes):
                raise TypeError("file_bytes is not a bytes object")
            file_bytes.seek(0)

            if mime_type.startswith("text/") or mode in ["snippet", "post"]:
                with closing(file_bytes):
                    extracted_text = file_bytes.getvalue().decode("utf-8")
                transformed_message.add_text(f"From {file_name}: \n{extracted_text}\n")

            elif mime_type == "application/pdf":
                await self.process_pdf(file_bytes, transformed_message)

            elif mime_type.startswith("image/"):
                await self.process_image(file_type, file_bytes, transformed_message)

            elif mime_type.startswith("audio/"):
                await self.process_audio(file_type, file_bytes, transformed_message)

    async def process_pdf(self, file_bytes, transformed_message):
        file_bytes.seek(0)
        try:
            pdf_reader = pypdf.PdfReader(file_bytes)
            file_bytes.seek(0)
            file_type, images_bytes = pdf_to_images(file_bytes)
            for image in images_bytes:
                transformed_message.add_file(ProcessedFile(file_type, image))
        except pypdf.errors.PdfStreamError as e:
            logger.error(f"Stream error while reading PDF file: {e}")
        except pypdf.errors.ParseError as e:
            logger.error(f"Parse error in PDF file: {e}")
        except pypdf.errors.PageSizeNotDefinedError as e:
            logger.error(f"Page size not defined in PDF file: {e}")
        except pypdf.errors.WrongPasswordError:
            logger.error("Wrong password provided for encrypted PDF file.")
        except pypdf.errors.FileNotDecryptedError:
            logger.error(
                "PDF file is encrypted and cannot be decrypted without a password."
            )
        except pypdf.errors.EmptyFileError:
            logger.error("PDF file is empty or corrupted.")
        except pypdf.errors.PdfReadError as e:
            logger.error(f"Failed to read PDF file: {e}")
        except pypdf.PyPdfError as e:
            logger.error(f"PDF processing error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing PDF: {e}")

    async def process_image(self, file_type, file_bytes, transformed_message):
        if file_type not in self.supported_image_types:
            file_bytes.seek(0)
            converted_file_type, converted_file_bytes = await convert_image_to_png(
                file_type, file_bytes
            )
            file_bytes.seek(0)
            transformed_message.add_file(
                ProcessedFile(converted_file_type, converted_file_bytes)
            )
        else:
            transformed_message.add_file(ProcessedFile(file_type, file_bytes))

    async def process_audio(self, file_type, file_bytes, transformed_message):
        if file_type not in self.supported_audio_types:
            file_bytes.seek(0)
            converted_file_type, converted_file_bytes = await convert_audio_to_mp3(
                file_type, file_bytes
            )
            converted_file_bytes.seek(0)
            transcribed_text = await self.transcription_model.call_model(
                converted_file_type, converted_file_bytes
            )
        else:
            transcribed_text = await self.transcription_model.call_model(
                file_type, file_bytes
            )

        transformed_message.add_text(
            f"Transcription from audio file:\n{transcribed_text}\n"
        )
