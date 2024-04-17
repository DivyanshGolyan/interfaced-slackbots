from app.agents.agent_manager import Agent
from app.ml_models.dalle import DALLE
from app.ml_models.whisper import Whisper
from app.utils.file_utils import *
from app.objects import *
from contextlib import closing
import pypdf
import pypdf.errors
from app.config import *
from app.adapters.gpt_adapter import GPTAdapter
import asyncio
from app.exceptions import *
from app.utils.stream_to_message import *


class DALLE(Agent):
    def __init__(self):
        self.supported_mime_categories = []
        self.supported_image_types = []
        self.supported_audio_types = []
        self.end_model = DALLE()

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

        # Call the external stream handling function and yield from it
        async for response in handle_stream(self.end_model, payload, stream=True):
            yield response

    async def process_message(self, message):
        if not isinstance(message, slack_message):
            raise TypeError("message is not a slack_message object")

        transformed_message = TransformedSlackMessage(
            message.user_id, message.bot_user_id
        )
        transformed_message.add_text(message.text)

        return transformed_message
