from pdf2image import convert_from_bytes
import io
import base64
from app.config import logger
from pydub import AudioSegment
from PIL import Image
from app.exceptions import *
from typing import *


async def pdf_to_images(pdf_bytes: bytes) -> Tuple[str, List[bytes]]:
    try:
        images = convert_from_bytes(pdf_bytes)
        images_bytes = []
        for image in images:
            if image.size[0] * image.size[1] > Image.MAX_IMAGE_PIXELS:
                logger.error("Image size exceeds the default PIL pixel limit.")
                raise PDFToImageConversionError(
                    "Image size exceeds the default safe limit and could be a decompression bomb."
                )
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            images_bytes.append(buffer.getvalue())
            image.close()  # Close the image to free up memory
        del pdf_bytes  # Explicitly delete the pdf_bytes to free up memory
        return "jpeg", images_bytes
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        raise PDFToImageConversionError(
            "We encountered an issue while preparing your using your PDF. Please ensure your PDF is not corrupted and try again."
        )


async def image_bytes_to_base64(image_bytes: bytes) -> str:
    try:
        base64_string = base64.b64encode(image_bytes).decode("utf-8")
        del image_bytes  # Delete the original image bytes to free up memory
        return base64_string
    except Exception as e:
        logger.error(f"Error converting image bytes to base64: {e}")
        raise ImageProcessingError(
            "We encountered an issue while processing your image. Please ensure your image is in a supported format and try again."
        )


async def convert_audio_to_mp3(file_type, file_bytes):
    try:
        # Ensure file_bytes is a file-like object
        if isinstance(file_bytes, bytes):
            file = io.BytesIO(file_bytes)
            file.seek(0)
            format = file_type
            audio = AudioSegment.from_file(file, format=format)
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format="mp3")
            mp3_data = output_buffer.getvalue()
            del file_bytes
            del file  # Delete the original file bytes to free up memory
            return "mp3", mp3_data
    except Exception as e:
        logger.error(f"Error converting audio to MP3: {e}")
        raise e


async def convert_image_to_png(file_type, file_bytes):
    try:
        # Ensure file_bytes is a file-like object
        if isinstance(file_bytes, bytes):
            file = io.BytesIO(file_bytes)
            file.seek(0)
            image = Image.open(file)
            if image.mode not in ["RGB", "RGBA"]:
                image = image.convert("RGBA")

            png_buffer = io.BytesIO()
            image.save(png_buffer, format="PNG")
            png_bytes = png_buffer.getvalue()
            del file_bytes  # Delete the original file bytes to free up memory
            del file
            return "png", png_bytes
    except Exception as e:
        logger.error(f"Error converting {file_type} image to png: {e}")
        raise e
