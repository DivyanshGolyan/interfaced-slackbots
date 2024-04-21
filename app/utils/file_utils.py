from pdf2image import convert_from_bytes
import io
import base64
from app.config import *
from pydub import AudioSegment
from PIL import Image
from app.exceptions import *
from typing import *

# import hashlib
from app.LLM_clients.google_client import genai as google_client
import cv2
import io
from typing import List, Tuple
import tempfile
import pathlib
import aiofiles

# import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# import aiohttp
# import uuid
# import json
import traceback


async def pdf_to_images(
    pdf_bytes: bytes, max_width: int = 1024, max_height: int = 1024
) -> Tuple[str, List[bytes]]:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with ProcessPoolExecutor() as process_executor:
                future = process_executor.submit(
                    convert_from_bytes, pdf_bytes, output_folder=temp_dir, fmt="jpeg"
                )
                images = future.result()

            with ThreadPoolExecutor() as thread_executor:
                resize_tasks = []
                for image in images:
                    task = thread_executor.submit(
                        resize_image, image, max_width, max_height
                    )
                    resize_tasks.append(task)

                images_bytes = [task.result() for task in resize_tasks]

        del pdf_bytes
        return "jpeg", images_bytes
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}\n{traceback.format_exc()}")
        raise PDFToImageConversionError(
            "We encountered an issue while preparing your using your PDF. Please ensure your PDF is not corrupted and try again."
        )


def resize_image(image, max_width, max_height):
    original_width, original_height = image.size
    ratio = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    image = image.resize((new_width, new_height))

    if image.size[0] * image.size[1] > Image.MAX_IMAGE_PIXELS:
        logger.error("Image size exceeds the default PIL pixel limit.")
        raise PDFToImageConversionError(
            "Image size exceeds the default safe limit and could be a decompression bomb."
        )

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


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


async def base64_to_image_bytes(base64_string: str) -> bytes:
    try:
        image_bytes = base64.b64decode(base64_string)
        return image_bytes
    except Exception as e:
        logger.error(f"Error converting base64 to image bytes: {e}")
        raise ImageProcessingError(
            "We encountered an issue while processing your base64 string. Please ensure it is correctly formatted and try again."
        )


async def convert_audio_to_mp3(file_type, file_bytes):
    if not isinstance(file_bytes, bytes):
        raise TypeError("file_bytes must be of type bytes")
    try:
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


def get_mime_type_from_url(file_type, media_display_type):
    """
    Extracts the file extension from the URL and returns the corresponding MIME type,
    considering the media display type (audio or video).
    """

    file_type
    mime_type_entry = file_type_to_mime_type.get(file_type)

    if isinstance(mime_type_entry, dict):
        # If the entry is a dictionary, use the media_display_type to determine the specific MIME type
        return mime_type_entry.get(media_display_type)
    else:
        return mime_type_entry


async def google_upload(file_bytes: bytes, file_type: str) -> str:
    try:
        # Create a temporary file to save the bytes with the file_type as the suffix
        async with aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_type}"
        ) as tmp_file:
            await tmp_file.write(file_bytes)
            tmp_file_path = pathlib.Path(tmp_file.name)

        uploaded_file = google_client.upload_file(path=tmp_file_path)

        # Clean up the temporary file after uploading
        tmp_file_path.unlink()

        return uploaded_file.uri
    except Exception as e:
        logger.error(f"Error handling file in Google Cloud: {e}")
        raise GeminiError(e)


# async def google_upload_http(file_bytes: bytes, file_type: str) -> str:

#     url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
#     headers = {
#         "Authorization": f"Bearer {GOOGLE_API_KEY}",
#         "Content-Type": "application/octet-stream",
#     }
#     random_file_name = f"{uuid.uuid4()}.{file_type}"
#     params = {"uploadType": "media", "name": random_file_name}

#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             url, headers=headers, params=params, data=file_bytes
#         ) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 return data["uri"]
#             else:
#                 response_text = await response.text()
#                 raise Exception(
#                     f"Failed to upload file: {response.status} {response_text}"
#                 )


# async def google_upload_http(
#     file_bytes: bytes, file_type: str, file_name: str = None
# ) -> str:
#     url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
#     headers = {
#         "Authorization": f"Bearer {GOOGLE_API_KEY}",
#     }

#     # Prepare file metadata
#     file_metadata = {}
#     if file_name:
#         file_metadata["name"] = file_name

#     # Create multipart form data
#     data = aiohttp.FormData()
#     data.add_field("file", json.dumps(file_metadata), content_type="application/json")
#     data.add_field(
#         "media",
#         file_bytes,
#         filename=f"{uuid.uuid4()}.{file_type}",
#         content_type="application/octet-stream",  # Adjust MIME type if known
#     )

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, headers=headers, data=data) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 return data["uri"]
#             else:
#                 response_text = await response.text()
#                 logger.error(response)
#                 raise Exception(f"Failed to upload file: {response}")


# async def google_upload_async_http(file_bytes: bytes, file_type: str) -> str:
#     """Uploads file bytes asynchronously using aiohttp and a temporary file.

#     Args:
#         file_bytes (bytes): The file content as bytes.
#         file_type (str): The file type (e.g., "txt", "png").
#         api_key (str): Your Google Cloud API key.

#     Returns:
#         str: The URI of the uploaded file.
#     """
#     try:
#         async with aiofiles.tempfile.NamedTemporaryFile(
#             delete=False, suffix=f".{file_type}"
#         ) as tmp_file:
#             await tmp_file.write(file_bytes)
#             tmp_file_path = pathlib.Path(tmp_file.name)

#         url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
#         headers = {
#             "Authorization": f"Bearer {GOOGLE_API_KEY}",
#             "Content-Type": "multipart/related",
#         }

#         # Create multipart form data with mimeType
#         data = aiohttp.FormData()
#         mime_type = file_type_to_mime_type.get(file_type)
#         data.add_field(
#             "file",
#             json.dumps({"mimeType": mime_type}),
#             content_type="application/json",
#         )
#         data.add_field(
#             "media",
#             open(tmp_file_path, "rb"),
#             filename=tmp_file_path.name,
#             content_type=mime_type,
#         )

#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers, data=data) as response:
#                 response_data = await response.json()
#                 uri = response_data["file"]["uri"]

#         # Clean up the temporary file
#         tmp_file_path.unlink()

#         return uri

#     except Exception as e:
#         # Handle exceptions and logging as needed
#         logger.error(f"Error handling file in Google Cloud: {e}")
#         raise GeminiError(e)


async def extract_frames_from_video_bytes(
    video_bytes: bytes,
    file_type: str,
    frames_per_second: int = 1,
    image_format: str = ".jpg",
) -> List[Tuple[bytes, str, str]]:
    try:
        # Create a temporary file to write video bytes
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_type}"
        ) as temp_video_file:
            temp_video_file.write(video_bytes)
            temp_video_file_name = temp_video_file.name

        # Initialize video capture from the temporary file
        vidcap = cv2.VideoCapture(temp_video_file_name)
        fps = vidcap.get(cv2.CAP_PROP_FPS)  # Frames per second in the video
        duration = vidcap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

        max_duration = (
            VIDEO_PROCESSING_DURATION_LIMIT  # Maximum allowed duration in seconds
        )

        if duration > max_duration:
            raise VideoProcessingError(
                f"Your video is {duration:.2f} seconds long, which exceeds the maximum allowed duration of {max_duration} seconds. Please upload a shorter video."
            )

        frames_data = []
        count = 0

        # Calculate frame extraction rate
        frame_extraction_rate = (
            int(fps / frames_per_second) if fps >= frames_per_second else 1
        )

        while vidcap.isOpened():
            success, frame = vidcap.read()
            if not success:  # End of video
                break
            if (
                count % frame_extraction_rate == 0
            ):  # Extract frames based on the calculated rate
                # Encode frame to specified image format
                success, encoded_image = cv2.imencode(
                    image_format, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95]
                )
                if success:
                    # Convert the encoded image to bytes
                    image_bytes = encoded_image.tobytes()

                    # Calculate timestamp
                    seconds = count / fps
                    timestamp = f"{int(seconds // 3600):02d}:{int((seconds % 3600) // 60):02d}:{int(seconds % 60):02d}"

                    # Append image bytes, timestamp, and image format (without the dot)
                    frames_data.append(
                        (image_bytes, timestamp, image_format.strip("."))
                    )
            count += 1

        vidcap.release()  # Release the capture object
        os.unlink(temp_video_file_name)  # Clean up the temporary file
        return frames_data
    except Exception as e:
        logger.error(f"Error extracting frames from video bytes: {e}")
        raise e
