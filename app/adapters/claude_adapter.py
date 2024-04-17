from app.adapters.base_adapter import LLMAdapter
from app.utils.file_utils import image_bytes_to_base64
from app.config import file_type_to_mime_type
import asyncio
from app.exceptions import *


class ClaudeAdapter(LLMAdapter):
    async def convert_conversation(self, conversation):
        bot_user_id = conversation.messages[0].bot_user_id
        system_prompt = f"""You are an autoregressive language model that has been fine-tuned with instruction-tuning and RLHF. You carefully provide accurate, factual, thoughtful, nuanced answers, and are brilliant at reasoning. If you think there might not be a correct answer, you say so. Since you are autoregressive, each token you produce is another opportunity to use computation, therefore you always spend a few sentences explaining background context, assumptions, and step-by-step thinking BEFORE you try to answer a question. Your users are experts in AI and ethics, so they already know you're a language model and your capabilities and limitations, so don't remind them of that. They're familiar with ethical issues in general so you don't need to remind them about those either. Don't be verbose in your answers, but do provide details and examples where it might help the explanation. If you have text that you want to be bolded, surround it with single asterisks (*). DO NOT EVER USE DOUBLE ASTERISKS (**). Best not use them.] For italics, use single underscores (_). To strike through text, use single tildes (~). If you have text that you want to be highlighted like code, surround it with back-tick (`) characters. You can also highlight larger, multi-line code blocks by placing 3 back-ticks before and after the block. I am sending you a thread of slack messages. Your user_id: {bot_user_id}. If you refer to users in your response, please use the following syntax: <@user_id>. For example: <@U024BE7LH>. You can use emojies if you want to."""
        messages = await asyncio.gather(
            *[self.convert_message(msg) for msg in conversation.messages]
        )
        result = (system_prompt, messages)
        return result

    async def convert_message(self, message):
        user_id = message.user_id
        bot_user_id = message.bot_user_id
        if user_id == bot_user_id:
            role = "assistant"
        else:
            role = "user"
        content = []
        if message.text:
            # Using an array of content blocks with type "text"
            content.append({"type": "text", "text": message.text})
        files = message.files
        for file in files:
            file_type = file.file_type
            if file_type in ["png", "jpeg", "jpg", "webp", "gif"]:
                mime_type = file_type_to_mime_type.get(file_type)
                if mime_type is None:
                    raise ValueError(f"MIME type not found for file type: {file_type}")
                try:
                    base64_image = await image_bytes_to_base64(file.file_bytes)
                    # Adjusting image content to match the API's expected format
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        }
                    )
                except ImageProcessingError as e:
                    raise e
            else:
                raise ImageProcessingError(
                    f"Unsupported file type: {file_type}. Supported types are PNG, JPEG, JPG, WEBP, and GIF."
                )
        message = {"role": role, "content": content}
        return message
