class UserFacingError(Exception):
    """Base class for other exceptions"""

    pass


class PDFProcessingError(UserFacingError):
    """Raised when there is an issue with PDF processing."""

    pass


class PDFReadingError(PDFProcessingError):
    """Raised when there is an error reading the PDF file."""

    pass


class PDFToImageConversionError(PDFProcessingError):
    """Raised when there is an error converting the PDF to an image."""

    pass


class DataNotFoundError(UserFacingError):
    """Raised when required data is not found."""

    pass


class ImageProcessingError(UserFacingError):
    """Raised when there is an issue with image processing."""

    pass


class AudioProcessingError(UserFacingError):
    """Raised when there is an issue with audio processing."""

    pass


class OpenAIError(UserFacingError):
    """Raised when there is an issue with OpenAI services."""

    pass


class WhisperProcessingError(OpenAIError):
    """Raised when there is an issue with Whisper processing."""

    pass


class GPTProcessingError(OpenAIError):
    """Raised when there is an issue with GPT model processing."""

    pass


class GeminiError(UserFacingError):
    """Raised when there is an issue with Gemini services."""

    pass


class AnthropicError(UserFacingError):
    """Raised when there is an issue with Anthropic services."""

    pass


class StabilityError(UserFacingError):
    """Raised when there is a stability issue in the system."""

    pass
