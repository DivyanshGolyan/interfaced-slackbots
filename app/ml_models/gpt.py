from app.LLM_clients.openai_client import client as openai_client
import openai
import traceback
from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import *


class GPT(ModelWrapper):
    async def call_model(self, input_data, stream=False):
        model = GPT_MODEL
        try:
            if stream:
                response = await openai_client.chat.completions.create(
                    model=model, messages=input_data, stream=True
                )
                async for chunk in response:
                    yield chunk.choices[
                        0
                    ].delta.content  # Yield each chunk as it arrives
            else:
                response = await openai_client.chat.completions.create(
                    model=model, messages=input_data
                )
                choice = response.choices[0]
                message_content = choice.message.content
                yield message_content  # Return the complete message content

        except openai.APIConnectionError as e:
            logger.error("Connection error: The server could not be reached.")
            logger.error(f"Error details: {e}")
            raise

        except openai.RateLimitError:
            logger.error("Rate limit exceeded: Too many requests.")
            raise GPTProcessingError(
                "Rate limit exceeded. Please wait before sending more requests."
            )

        except openai.BadRequestError as e:
            logger.error("Bad request error: A 400 status code was received.")
            if "context_length_exceeded" in str(e):
                raise GPTProcessingError(
                    "The conversation is too long. Please reduce the length and try again."
                )
            else:
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

        except openai.UnprocessableEntityError:
            logger.error(
                "Unprocessable entity error: The request could not be processed."
            )
            raise GPTProcessingError(
                "The request could not be processed. Please modify your input and try again."
            )

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
            logger.error("An unexpected error occurred.")
            logger.error(traceback.format_exc())
            raise GPTProcessingError(f"An unexpected error occurred: {e}")
