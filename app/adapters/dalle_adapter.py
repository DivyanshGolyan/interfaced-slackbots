from app.adapters.base_adapter import LLMAdapter
from app.utils.file_utils import image_bytes_to_base64
from app.config import file_type_to_mime_type
import asyncio
from app.exceptions import *


class DALLEAdapter(LLMAdapter):
    async def convert_conversation(self, conversation):
        prompt = await asyncio.gather(
            *[self.convert_message(msg) for msg in conversation.messages]
        )
        return " \n ".join(prompt)

    async def convert_message(self, message):
        user_id = message.user_id
        bot_user_id = message.bot_user_id
        if user_id == bot_user_id:
            role = "assistant"
        else:
            role = "user"
        prompt_text = ""
        if message.text:
            prompt_text = f"{role}: {message.text}"
        return prompt_text
