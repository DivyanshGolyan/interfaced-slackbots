from app.agents.agent_manager import Agent
from app.ml_models.dalle import DALLE as DALLE_model
from app.utils.file_utils import *
from app.objects import *
from app.config import *
from app.adapters.dalle_adapter import DALLEAdapter
import asyncio
from app.exceptions import *
from app.utils.stream_to_message import *


class DALLE(Agent):
    def __init__(self):
        self.supported_mime_categories = []
        self.supported_image_types = []
        self.supported_audio_types = []
        self.model_adapter = DALLEAdapter()
        self.end_model = DALLE_model()

    async def process_conversation(self, conversation):
        if not isinstance(conversation, slack_conversation):
            raise TypeError("conversation is not a slack_conversation object")

        transformed_conversation = TransformedSlackConversation()

        transformed_messages = await asyncio.gather(
            *(self.process_message(message) for message in conversation.messages)
        )

        for transformed_message in transformed_messages:
            transformed_conversation.add_message(transformed_message)

        prompt = await self.model_adapter.convert_conversation(transformed_conversation)

        revised_prompt, image_base64 = await self.end_model.call_model(prompt)

        image_bytes = await base64_to_image_bytes(image_base64)
        pixel_count = await get_image_pixel_count(image_bytes)
        agent_response = AgentResponse(
            text=f"Generated with the following detailed prompt: _{revised_prompt}_",
            is_stream=False,
        )
        agent_response.add_file(
            AgentResponseFile(
                file_bytes=image_bytes,
                filename="generated_image.png",
                properties={"pixel_count": pixel_count},
                mime_type="image/png",
            )
        )

        yield agent_response

    async def process_message(self, message):
        if not isinstance(message, slack_message):
            raise TypeError("message is not a slack_message object")

        transformed_message = TransformedSlackMessage(
            message.user_id, message.bot_user_id, message.ts
        )
        transformed_message.add_text(message.text)

        return transformed_message
