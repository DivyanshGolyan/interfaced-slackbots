from app.agents.agent_manager import Agent
from app.ml_models.stable_diffusion import StableDiffusion as SD
from app.utils.file_utils import *
from app.objects import *
from contextlib import closing
import pypdf
import pypdf.errors
from app.config import *
from app.adapters.stable_diffusion_adapter import SDAdapter
import asyncio
from app.exceptions import *
from app.utils.stream_to_message import *
from app.agents.chatgpt import ChatGPT


class StableDiffusion(Agent):
    def __init__(self):
        self.supported_image_types = ["png", "jpeg", "jpg", "webp"]
        self.prompt_generation_agent = ChatGPT()
        self.prompt_generation_system_prompt = """I want you to act as a Stable Diffusion Art Prompt Generator. The formula for a prompt is made of parts, the parts are indicated by brackets. The [Subject] is the person place or thing the image is focused on. [Emotions] is the emotional look the subject or scene might have. [Verb] is What the subject is doing, such as standing, jumping, working and other varied that match the subject. [Adjectives] like beautiful, rendered, realistic, tiny, colorful and other varied that match the subject. The [Environment] in which the subject is in, [Lighting] of the scene like moody, ambient, sunny, foggy and others that match the Environment and compliment the subject. [Photography type] like Polaroid, long exposure, monochrome, GoPro, fisheye, bokeh and others. And [Quality] like High definition, 4K, 8K, 64K UHD, SDR and other. The subject and environment should match and have the most emphasis. It is ok to omit one of the other formula parts. I will give you a conversation and you will respond with a full prompt. Present the result as one full sentence, no line breaks, no delimiters, and keep it as concise as possible while still conveying a full scene. Here is a sample of how it should be output: 'Beautiful woman, contemplative and reflective, sitting on a bench, cozy sweater, autumn park with colorful leaves, soft overcast light, muted color photography style, 4K quality.'"""
        self.model_adapter = SDAdapter()
        self.end_model = SD()

    async def process_conversation(self, conversation):
        if not isinstance(conversation, slack_conversation):
            raise TypeError("conversation is not a slack_conversation object")

        prompt = ""
        async for part in self.prompt_generation_agent.process_conversation(
            conversation, self.prompt_generation_system_prompt, False
        ):
            prompt += part.text

        print(f"Stable Diffusion Prompt: {prompt}")

        transformed_conversation = TransformedSlackConversation()

        transformed_messages = await asyncio.gather(
            *(self.process_message(message) for message in conversation.messages)
        )

        for transformed_message in transformed_messages:
            transformed_conversation.add_message(transformed_message)

        input_image_bytes = await self.model_adapter.convert_conversation(
            transformed_conversation
        )

        output_image_bytes = await self.end_model.call_model(
            prompt=prompt, image=input_image_bytes
        )

        agent_response = AgentResponse(
            text=f"Generated with the following detailed prompt: _{prompt}_",
            is_stream=False,
        )
        agent_response.add_file(
            AgentResponseFile(
                file_bytes=output_image_bytes, filename="generated_image.png"
            )
        )

        yield agent_response

    async def process_message(self, message):
        if not isinstance(message, slack_message):
            raise TypeError("message is not a slack_message object")

        transformed_message = TransformedSlackMessage(
            message.user_id, message.bot_user_id
        )

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
        file_type = file.filetype

        if mime_type.startswith("image/"):
            file_bytes = await message.get_file_content(file)
            if not isinstance(file_bytes, bytes):
                raise TypeError("file_bytes is not a bytes object")
            await self.process_image(file_type, file_bytes, transformed_message)

    async def process_image(self, file_type, file_bytes, transformed_message):
        if file_type not in self.supported_image_types:
            converted_file_type, converted_file_bytes = await convert_image_to_png(
                file_type, file_bytes
            )
            transformed_message.add_file(
                ProcessedFile(converted_file_type, converted_file_bytes)
            )
        else:
            transformed_message.add_file(ProcessedFile(file_type, file_bytes))
