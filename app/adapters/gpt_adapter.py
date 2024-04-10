from app.adapters.base_adapter import LLMAdapter
from app.utils.file_transformations import image_bytes_to_base64


class GPTAdapter(LLMAdapter):
    async def convert_conversation(self, conversation):
        return [await self.convert_message(msg) for msg in conversation.messages]

    async def convert_message(self, message):
        user_id = message.user_id
        bot_user_id = message.bot_user_id
        if user_id == bot_user_id:
            role = "assistant"
        else:
            role = "user"
        content = []
        if message.text:
            content.append({"type": "text", "text": message.text})
        files = message.files
        for file in files:
            mime_type = file.mime_type
            if mime_type in ["image/png", "image/jpeg", "image/webp", "image/gif"]:
                base64_image = await image_bytes_to_base64(file.file_bytes)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    }
                )
            else:
                raise TypeError(f"Unsupported MIME type: {mime_type}")
        message = {"role": role, "content": content}
        return message
