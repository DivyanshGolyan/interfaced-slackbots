from app.LLM_clients.anthropic_client import client as anthropic_client
import anthropic
import traceback
from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import *


class Claude(ModelWrapper):
    async def call_model(self, input_data, stream=False):
        model = CLAUDE_MODEL
        system_prompt, messages = (
            input_data  # Unpack the tuple into system prompt and messages
        )
        try:
            if stream:
                async with anthropic_client.messages.stream(
                    model=model,
                    system=system_prompt,
                    messages=messages,
                    max_tokens=4096,
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
                    yield None
            else:
                response = await anthropic_client.messages.create(
                    model=model,
                    system=system_prompt,
                    messages=messages,
                    max_tokens=4096,
                )
                message_content = response.content
                yield message_content  # Return the complete message content

        except anthropic.APIConnectionError as e:
            logger.error("Connection error: The server could not be reached.")
            logger.error(f"Error details: {e}")
            raise AnthropicError("Connection error: The server could not be reached.")

        except anthropic.RateLimitError:
            logger.error("Rate limit exceeded: Too many requests.")
            raise AnthropicError(
                "Rate limit exceeded. Please wait before sending more requests."
            )

        except anthropic.BadRequestError as e:
            logger.error("Bad request error: A 400 status code was received.")
            if "context_length_exceeded" in str(e):
                raise AnthropicError(
                    "The conversation is too long. Please reduce the length and try again."
                )
            elif "Your credit balance is too low" in str(e):
                raise AnthropicError(
                    "It seems there's an issue with the credit balance needed for the Claude API. Please contact support for assistance."
                )
            else:
                raise e

        except anthropic.AuthenticationError as e:
            logger.error(
                "Authentication error: A 401 status code was received; Authentication failed."
            )
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except anthropic.PermissionDeniedError as e:
            logger.error("Permission denied error: A 403 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except anthropic.NotFoundError as e:
            logger.error("Not found error: A 404 status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except anthropic.UnprocessableEntityError:
            logger.error(
                "Unprocessable entity error: The request could not be processed."
            )
            raise AnthropicError(
                "The request could not be processed. Please modify your input and try again."
            )

        except anthropic.InternalServerError as e:
            logger.error(
                "Internal server error: A 500 status code or above was received."
            )
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except anthropic.APIStatusError as e:
            logger.error("API status error: A non-200-range status code was received.")
            logger.error(f"Status code: {e.status_code}, Response: {e.response}")
            raise e

        except Exception as e:
            logger.error("An unexpected error occurred.")
            logger.error(traceback.format_exc())
            raise AnthropicError(f"An unexpected error occurred: {e}")
