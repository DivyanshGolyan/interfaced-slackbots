from app.agents.agent_manager import Agent
from app.ml_models.claude import Claude as Claude_model
from app.ml_models.whisper import Whisper
from app.utils.file_utils import *
from app.objects import *
from contextlib import closing
import pypdf
import pypdf.errors
from app.config import *
from app.adapters.claude_adapter import ClaudeAdapter
import asyncio
from app.exceptions import *
from app.utils.stream_to_message import *
from app.database.dao import *


class Claude(Agent):
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
        self.model_adapter = ClaudeAdapter()
        self.end_model = Claude_model()

    async def process_conversation(self, conversation, system_prompt=None, stream=True):
        if not isinstance(conversation, slack_conversation):
            raise TypeError("conversation is not a slack_conversation object")

        transformed_conversation = TransformedSlackConversation()

        transformed_messages = await asyncio.gather(
            *(self.process_message(message) for message in conversation.messages)
        )

        for transformed_message in transformed_messages:
            transformed_conversation.add_message(transformed_message)

        payload = await self.model_adapter.convert_conversation(
            transformed_conversation, system_prompt
        )

        if stream:
            # Call the external stream handling function and yield from it
            async for response in handle_stream(self.end_model, payload, stream=stream):
                yield response
        else:
            # Call the model directly and yield the response as an agent response
            async for response in self.end_model.call_model(payload, stream=False):
                yield AgentResponse(text=response, is_stream=False, end_of_stream=True)

    async def process_message(self, message):
        if not isinstance(message, slack_message):
            raise TypeError("message is not a slack_message object")

        transformed_message = TransformedSlackMessage(
            message.user_id, message.bot_user_id, message.ts
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

        if not isinstance(file, slack_file):
            raise TypeError("file is not a slack_file object")

        mime_type = file.mimetype
        mode = file.mode
        file_name = file.name
        file_type = file.filetype
        slack_file_id = file.id

        if any(
            mime_type.startswith(category)
            for category in self.supported_mime_categories
        ) or mode in ["snippet", "post"]:
            file_bytes = await message.get_file_content(file)
            if not isinstance(file_bytes, bytes):
                raise TypeError("file_bytes is not a bytes object")

            if mime_type.startswith("text/") or mode in ["snippet", "post"]:
                extracted_text = file_bytes.decode("utf-8")
                message_text = f"From {file_name}: \n{extracted_text}\n"
                await transformed_message.add_text(message_text)
                await append_message_text(message.message_ts, message_text)

            elif mime_type == "application/pdf":
                await self.process_pdf(file_bytes, transformed_message, slack_file_id)

            elif mime_type.startswith("image/"):
                await self.process_image(
                    file_type, file_bytes, transformed_message, slack_file_id
                )

            elif mime_type.startswith("audio/"):
                await self.process_audio(
                    file_type, file_bytes, transformed_message, slack_file_id
                )

    async def process_pdf(self, file_bytes, transformed_message, slack_file_id):
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(pdf_reader.pages)
            if page_count > PDF_PAGE_LIMIT:
                raise PDFProcessingError(
                    f"Your PDF has {page_count} pages, which exceeds the {PDF_PAGE_LIMIT}-page limit."
                )
            file_type, images_bytes, pixel_count = await pdf_to_images(
                file_bytes, slack_file_id
            )
            for image in images_bytes:
                transformed_message.add_file(
                    ProcessedFile(file_type, image, slack_file_id=slack_file_id)
                )
            await update_file(
                slack_file_id,
                properties={"page_count": page_count, "pixel_count": pixel_count},
            )
            del pdf_reader
        except (
            pypdf.errors.PdfStreamError,
            pypdf.errors.ParseError,
            pypdf.errors.PageSizeNotDefinedError,
            pypdf.errors.WrongPasswordError,
            pypdf.errors.FileNotDecryptedError,
            pypdf.errors.EmptyFileError,
            pypdf.errors.PdfReadError,
        ) as e:
            logger.error(f"PDF reading error: {e}")
            raise PDFReadingError(
                "There was an error processing the PDF file. Please ensure the file is not corrupted or encrypted with an unknown password."
            )
        except PDFToImageConversionError as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing PDF: {e}")
            raise e

    async def process_image(
        self, file_type, file_bytes, transformed_message, slack_file_id
    ):
        if file_type not in self.supported_image_types:
            converted_file_type, converted_file_bytes = await convert_image_to_png(
                file_type, file_bytes
            )
            transformed_message.add_file(
                ProcessedFile(
                    converted_file_type,
                    converted_file_bytes,
                    slack_file_id=slack_file_id,
                )
            )
            pixel_count = await get_image_pixel_count(converted_file_bytes)
        else:
            transformed_message.add_file(
                ProcessedFile(file_type, file_bytes, slack_file_id=slack_file_id)
            )
            pixel_count = await get_image_pixel_count(file_bytes)

        # Update the pixel_count in the database
        await update_file(slack_file_id, properties={"pixel_count": pixel_count})

    async def process_audio(
        self, file_type, file_bytes, transformed_message, slack_file_id
    ):
        if file_type not in self.supported_audio_types:
            try:
                converted_file_type, converted_file_bytes = await convert_audio_to_mp3(
                    file_type, file_bytes
                )
            except Exception as e:
                logger.error(f"Error converting audio to MP3: {e}")
                supported_formats = ", ".join(self.supported_audio_types)
                raise AudioProcessingError(
                    f"Failed to convert the audio file to MP3 format, which is supported. Please ensure your file is in a compatible format and try again. Supported formats include: {supported_formats}."
                )
            audio_length = await get_audio_length(
                converted_file_bytes, converted_file_type
            )
            transcribed_text = await self.transcription_model.call_model(
                converted_file_type, converted_file_bytes
            )
        else:
            audio_length = await get_audio_length(file_bytes, file_type)
            transcribed_text = await self.transcription_model.call_model(
                file_type, file_bytes
            )

        await transformed_message.add_text(
            f"Transcription from audio file:\n{transcribed_text}\n"
        )

        # Update the audio duration in the database
        await update_file(
            slack_file_id, properties={"audio_duration_seconds": audio_length}
        )
