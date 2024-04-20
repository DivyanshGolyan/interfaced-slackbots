from app.adapters.base_adapter import LLMAdapter
from app.config import file_type_to_mime_type
import asyncio
from app.exceptions import *
from app.utils.file_utils import *


class GeminiAdapter(LLMAdapter):
    async def convert_conversation(self, conversation):
        tasks = [self.convert_message(message) for message in conversation.messages]
        messages_parts = await asyncio.gather(*tasks)
        contents = [
            {
                "parts": parts,
                "role": ("user" if message.user_id != message.bot_user_id else "model"),
            }
            for parts, message in zip(messages_parts, conversation.messages)
        ]
        return contents

    async def convert_message(self, message):
        parts = []
        if message.text:
            parts.append({"text": message.text})
        for file in message.files:
            file_parts = await self.process_file(file)
            parts.extend(file_parts)
        return parts

    async def process_file(self, file):
        file_type = file.file_type
        supported_image_types = ["png", "jpeg", "jpg", "webp", "heic", "heif"]
        supported_audio_types = ["wav", "mp3", "aiff", "aac", "ogg", "flac"]
        if file_type in supported_image_types + supported_audio_types:
            mime_type = file_type_to_mime_type.get(file_type)
            if mime_type is None:
                raise ValueError(f"MIME type not found for file type: {file_type}")
            try:
                result = []
                if file_type in supported_image_types:
                    # Use inline_data for images
                    blob = {"mime_type": mime_type, "data": file.file_bytes}
                    if file.description:
                        result.append({"text": file.description})
                    result.append({"inline_data": blob})
                else:
                    # Use file_data for audio files
                    file_uri = await google_upload(file.file_bytes, file_type)
                    file_data = {"mime_type": mime_type, "file_uri": file_uri}
                    if file.description:
                        result.append({"text": file.description})
                    result.append({"file_data": file_data})
                return result
            except Exception as e:
                raise FileProcessingError(f"Failed to process file: {str(e)}")
        else:
            raise FileProcessingError(
                f"Unsupported file type: {file_type}. Supported types are {supported_image_types + supported_audio_types}. Please upload a supported file type."
            )
