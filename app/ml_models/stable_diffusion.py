from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import SDProcessingError
import requests


from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import SDProcessingError
import requests


class StableDiffusion(ModelWrapper):
    API_ENDPOINT = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    MODEL = "sd3"
    OUTPUT_FORMAT = "png"
    HEADERS = {
        "authorization": f"Bearer {STABILITY_API_KEY}",
        "accept": "image/*",  # or "application/json" based on your needs
    }
    STRENGTH = 0.8

    async def call_model(self, prompt, image=None):
        mode = "image-to-image" if image else "text-to-image"
        data = {
            "prompt": prompt,
            "negative_prompt": "nude, nsfw",
            "mode": mode,
            "output_format": self.OUTPUT_FORMAT,
            "model": self.MODEL,
        }
        if mode == "image-to-image":
            data.update({"strength": self.STRENGTH, "image": image})
        elif mode == "text-to-image":
            data.update({"aspect_ratio": "1:1"})

        return await self.make_request(self.HEADERS, data)

    async def make_request(self, headers, data):
        try:
            if "image" in data:
                # Ensure the image is passed correctly in the files parameter
                image_file = data.pop("image")
                files = {
                    "image": image_file
                }  # 'image' is the form field name for the file
            else:
                files = {"none": ""}

            response = requests.post(
                self.API_ENDPOINT, headers=headers, data=data, files=files
            )
            if response.status_code == 200:
                return response.content
            else:
                error_info = response.json()
                error_name = error_info.get("name", "Unknown Error")
                error_details = ", ".join(
                    error_info.get("errors", ["No error details provided"])
                )
                error_message = f"Error: {error_name} - {error_details}"
                logger.error(f"HTTP {response.status_code}: {error_message}")
                raise SDProcessingError(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"Network error: {str(e)}"
            logger.error(error_message)
            raise SDProcessingError(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            logger.error(error_message)
            raise SDProcessingError(
                "An unexpected error occurred while processing your request. Please try again later."
            )
