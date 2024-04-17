from app.LLM_clients.openai_client import client as openai_client
import openai
from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import DALLEProcessingError


class DALLE(ModelWrapper):
    async def call_model(self, prompt):
        try:
            if len(prompt) > 4000:  # Assuming dall-e-3 usage
                error_message = "Prompt length exceeds the maximum allowed characters (4000 for dall-e-3)"
                logger.error(error_message)
                raise DALLEProcessingError(error_message)
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

            return revised_prompt, image_base64

        except (
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.BadRequestError,
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.NotFoundError,
            openai.UnprocessableEntityError,
            openai.InternalServerError,
            openai.APIStatusError,
        ) as e:
            error_type = type(e).__name__.replace("Error", "")
            error_message = f"{error_type} error: {e}"
            logger.error(error_message)
            raise DALLEProcessingError(f"An error occurred: {error_message}")

        except DALLEProcessingError:
            raise
        except Exception as e:
            if "content_policy_violation" in str(e):
                logger.error(f"Content policy violation: {e}")
                raise DALLEProcessingError(
                    "Your request was rejected as a result of DALLE's safety system. Please try again with a modified prompt."
                )
            else:
                logger.error(f"An error occurred: {e}")
                raise DALLEProcessingError(
                    "An error occurred while processing your request. Please try again later."
                )
