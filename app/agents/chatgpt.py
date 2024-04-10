from agent_manager import Agent
from app.ml_models.gpt import GPT
from app.utils.file_transformations import pdf_to_images


class ChatGPT(Agent):
    def __init__(self):
        self.model = GPT()
        self.supported_types = {"text", "image", "PDF", "audio"}

    def can_process_input(self, input_data):
        return input_data["type"] in self.supported_types

    async def transform_input(self, input_data):
        if input_data["type"] == "PDF":
            return pdf_to_images(input_data["bytes"])
        else:
            return
