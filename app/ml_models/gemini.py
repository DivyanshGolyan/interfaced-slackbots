from app.LLM_clients.google_client import genai as google_client
import google.api_core.exceptions
import traceback
from app.ml_models.model_wrappers import ModelWrapper
from app.config import *
from app.exceptions import *


class Gemini(ModelWrapper):
    async def call_model(self, input_data, stream=False):
        model = google_client.GenerativeModel(GEMINI_MODEL)
        try:
            if stream:
                response = await model.generate_content_async(
                    contents=input_data, stream=True
                )
                async for chunk in response:
                    yield chunk.text  # Yield each chunk as it arrives
            else:
                response = await model.generate_content_async(contents=input_data)
                yield response.text  # Return the complete message content

            # Extract file URIs from input data and delete files
            file_uris = [
                part["file_data"]["file_uri"]
                for part in input_data[0]["parts"]
                if "file_data" in part
            ]
            for uri in file_uris:
                file_name = uri.split("/")[-1]  # Extract file name from URI
                google_client.delete_file(f"files/{file_name}")

        except google.api_core.exceptions.InvalidArgument as e:
            logger.error("Invalid argument error: The provided argument is not valid.")
            logger.error(f"Error details: {e}")
            raise GPTProcessingError(
                "Invalid argument provided. Please check your input and try again."
            )

        except google.api_core.exceptions.PermissionDenied as e:
            logger.error("Permission denied error: Access to the resource is denied.")
            logger.error(f"Error details: {e}")
            raise GPTProcessingError(
                "Permission denied. You do not have access to the requested resource."
            )

        except google.api_core.exceptions.ResourceExhausted as e:
            logger.error("Resource exhausted error: The quota has been exceeded.")
            logger.error(f"Error details: {e}")
            raise GPTProcessingError("Resource limit exceeded. Please try again later.")

        except google.api_core.exceptions.NotFound as e:
            logger.error("Not found error: The requested resource was not found.")
            logger.error(f"Error details: {e}")
            raise GPTProcessingError(
                "Resource not found. Please check the resource identifier and try again."
            )

        except google.api_core.exceptions.InternalServerError as e:
            logger.error("Internal server error: A server error occurred.")
            logger.error(f"Error details: {e}")
            raise GPTProcessingError("Internal server error. Please try again later.")

        except google.api_core.exceptions.ServiceUnavailable as e:
            logger.error(
                "Service unavailable error: The service is currently unavailable."
            )
            logger.error(f"Error details: {e}")
            raise GPTProcessingError(
                "Service is currently unavailable. Please try again later."
            )

        except Exception as e:
            logger.error("An unexpected error occurred.")
            logger.error(traceback.format_exc())
            raise GPTProcessingError(f"An unexpected error occurred: {e}")
