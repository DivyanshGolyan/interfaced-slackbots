from app.adapters.base_adapter import LLMAdapter
from app.exceptions import *


class SDAdapter(LLMAdapter):
    async def convert_conversation(self, conversation):
        all_files = []
        for message in conversation.messages:
            all_files.extend(message.files)
        last_file_file_bytes = all_files[-1].file_bytes if all_files else None
        return last_file_file_bytes

    async def convert_message(self, message):
        pass
