class UserFacingError(Exception):
    """Base class for other exceptions"""

    def __init__(self, message=None):
        super().__init__(message)
        self.message = message


class PDFProcessingError(UserFacingError):
    """Raised when there is an issue with PDF processing."""

    def __init__(self, message=None):
        super().__init__(message)


class PDFReadingError(PDFProcessingError):
    """Raised when there is an error reading the PDF file."""

    def __init__(self, message=None):
        super().__init__(message)


class PDFToImageConversionError(PDFProcessingError):
    """Raised when there is an error converting the PDF to an image."""

    def __init__(self, message=None):
        super().__init__(message)


class DataNotFoundError(UserFacingError):
    """Raised when required data is not found."""

    def __init__(self, message=None):
        super().__init__(message)


class ImageProcessingError(UserFacingError):
    """Raised when there is an issue with image processing."""

    def __init__(self, message=None):
        super().__init__(message)


class AudioProcessingError(UserFacingError):
    """Raised when there is an issue with audio processing."""

    def __init__(self, message=None):
        super().__init__(message)


class OpenAIError(UserFacingError):
    """Raised when there is an issue with OpenAI services."""

    def __init__(self, message=None):
        super().__init__(message)


class WhisperProcessingError(OpenAIError):
    """Raised when there is an issue with Whisper processing."""

    def __init__(self, message=None):
        super().__init__(message)


class GPTProcessingError(OpenAIError):
    """Raised when there is an issue with GPT model processing."""

    def __init__(self, message=None):
        super().__init__(message)


class DALLEProcessingError(OpenAIError):
    """Raised when there is an issue with DALL-E model processing."""

    def __init__(self, message=None):
        super().__init__(message)


class SDProcessingError(OpenAIError):
    """Raised when there is an issue with Stable Diffusion processing."""

    def __init__(self, message=None):
        super().__init__(message)


class GeminiError(UserFacingError):
    """Raised when there is an issue with Gemini services."""

    def __init__(self, message=None):
        super().__init__(message)


class AnthropicError(UserFacingError):
    """Raised when there is an issue with Anthropic services."""

    def __init__(self, message=None):
        super().__init__(message)


class StabilityError(UserFacingError):
    """Raised when there is a stability issue in the system."""

    def __init__(self, message=None):
        super().__init__(message)
