from LLM_clients.openai_client import client as openai_client
from config import logger
import openai
from model_wrappers import ModelWrapper
from app.config import DALLE_MODEL


class DALLE(ModelWrapper):
    async def call_model(self, input_data):
        prompt = input_data
        try:
            if len(prompt) > 4000:  # Assuming dall-e-3 usage
                with "Prompt length exceeds the maximum allowed characters (4000 for dall-e-3)" as e:
                    logger.error(e)
                    return (
                        e,
                        None,
                    )
            response = await openai_client.images.generate(
                model=DALLE_MODEL,
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                n=1,
                response_format="b64_json",
            )
            # Extract the base64 string from the response
            image_base64 = response.data[0].b64_json
            revised_prompt = response.data[0].revised_prompt
            # # Decode the base64 string into bytes
            # image_bytes = base64.b64decode(image_base64)
            # # Create an image from the bytes
            # image = Image.open(io.BytesIO(image_bytes))
            # # Save the image to a temporary file
            # temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            # image.save(temp_file.name)

            return revised_prompt, image_base64

        except openai.APIConnectionError as e:
            logger.error("Connection error: The server could not be reached.")
            logger.error(f"Error details: {e}")
            raise e

        except openai.RateLimitError as e:
            logger.error(
                "Rate limit exceeded: A 429 status code was received; we should back off a bit."
            )
            return None, None

        except openai.BadRequestError as e:
            logger.error("Bad request error: A 400 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.AuthenticationError as e:
            logger.error(
                "Authentication error: A 401 status code was received; Authentication failed."
            )
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.PermissionDeniedError as e:
            logger.error("Permission denied error: A 403 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.NotFoundError as e:
            logger.error("Not found error: A 404 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.UnprocessableEntityError as e:
            logger.error("Unprocessable entity error: A 422 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.InternalServerError as e:
            logger.error(
                "Internal server error: A 500 status code or above was received."
            )
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except openai.APIStatusError as e:
            logger.error("API status error: A non-200-range status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except Exception as e:
            if "content_policy_violation" in str(e):
                logger.error(f"Content policy violation: {e}")
                return (
                    "Your request was rejected as a result of our DALLE's safety system. Please try again with a modified prompt.",
                    None,
                )
            else:
                logger.error(f"An error occurred: {e}")
                return (
                    "An error occurred while processing your request. Please try again later.",
                    None,
                )
