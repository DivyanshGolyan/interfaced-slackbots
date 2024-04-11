from LLM_clients.openai_client import client as openai_client
from config import logger
import openai
import traceback
from model_wrappers import ModelWrapper
from app.config import GPT_MODEL


class GPT(ModelWrapper):
    async def call_model(self, input_data):
        model = GPT_MODEL
        try:
            response = await openai_client.chat.completions.create(
                model=model, messages=input_data
            )
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            message_content = choice.message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            if finish_reason == "length":
                return (
                    f">Error: The response was cut off due to exceeding the maximum token limit.\n{message_content}",
                    None,
                    None,
                )
            else:
                return message_content, prompt_tokens, completion_tokens

        except openai.APIConnectionError as e:
            logger.error("Connection error: The server could not be reached.")
            logger.error(f"Error details: {e}")
            raise e

        except openai.RateLimitError as e:
            logger.error(
                "Rate limit exceeded: A 429 status code was received; we should back off a bit."
            )
            return None, None, None

        except openai.BadRequestError as e:
            logger.error("Bad request error: A 400 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            if "context_length_exceeded" in str(e):
                return (
                    f"Error: The conversation is too long. Please reduce the length and try again.",
                    None,
                    None,
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
            logger.error("An unexpected error occurred.")
            logger.error(traceback.format_exc())
            return f"Error: {e}", None, None
