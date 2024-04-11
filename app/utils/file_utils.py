from pdf2image import convert_from_bytes
from typing import List
import io
import base64
from app.config import logger
from pydub import AudioSegment
from PIL import Image


async def pdf_to_images(pdf_bytes: bytes) -> List[bytes]:
    try:
        images = convert_from_bytes(pdf_bytes)
        images_bytes = []
        for image in images:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            images_bytes.append(buffer.getvalue())
            image.close()  # Close the image to free up memory
        del pdf_bytes  # Explicitly delete the pdf_bytes to free up memory
        return "jpeg", images_bytes
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        return None, []


async def image_bytes_to_base64(image_bytes: bytes) -> str:
    base64_string = base64.b64encode(image_bytes).decode("utf-8")
    del image_bytes  # Delete the original image bytes to free up memory
    return base64_string


async def convert_audio_to_mp3(file_type, file_bytes):
    try:
        format = file_type
        audio = AudioSegment.from_file(file_bytes, format=format)
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="mp3")
        mp3_data = output_buffer.getvalue()
        del file_bytes  # Delete the original file bytes to free up memory
        return "mp3", mp3_data
    except Exception as e:
        logger.error(f"Error converting audio to MP3: {e}")
        return None


async def convert_image_to_png(file_type, file_bytes):
    try:
        file_bytes.seek(0)
        image = Image.open(file_bytes)
        if image.mode not in ["RGB", "RGBA"]:
            image = image.convert("RGBA")

        png_buffer = io.BytesIO()
        image.save(png_buffer, format="PNG")
        png_bytes = png_buffer.getvalue()
        del file_bytes  # Delete the original file bytes to free up memory
        return "png", png_bytes
    except Exception as e:
        logger.error(f"Error converting {file_type} image to png: {e}")
        return None, None
