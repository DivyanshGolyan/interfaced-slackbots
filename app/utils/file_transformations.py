from pdf2image import convert_from_bytes
from typing import List
import io
import base64
from app.config import logger


async def pdf_to_images(pdf_bytes: bytes) -> List[bytes]:
    try:
        images = convert_from_bytes(pdf_bytes)
        images_bytes = []
        for image in images:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            images_bytes.append(buffer.getvalue())
        return images_bytes
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        return []


async def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
