import aiohttp
import io
from app.config import MAX_SLACK_FILE_SIZE
import magic


class slack_message:
    def __init__(self, message_data, bot_token, bot_user_id):
        self.bot_token = bot_token
        self.user_id = message_data.get("user")
        self.bot_user_id = bot_user_id
        self.ts = message_data.get("ts")
        self.text = message_data.get("text")
        self._files = message_data.get("files", [])
        self._file_contents = {}

    @property
    def files(self):
        return self._files.copy()

    async def get_file_content(self, file_metadata):
        file_url = file_metadata.get("url_private", "")
        file_size = file_metadata.get("size", 0)

        if not file_url:
            raise ValueError("File URL is missing")
        if file_size > MAX_SLACK_FILE_SIZE:
            raise ValueError(
                f"File size exceeds the limit of {MAX_SLACK_FILE_SIZE} bytes"
            )
        if file_url in self._file_contents:
            return self._file_contents[file_url]

        file_content = await self.download_file(file_url)
        self._file_contents[file_url] = file_content
        return file_content

    async def download_file(self, url):
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        async with aiohttp.ClientSession(
            headers=headers, timeout=aiohttp.ClientTimeout(total=300)
        ) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with io.BytesIO() as bytes_object:
                    bytes_object.write(await response.read())
                    bytes_object.seek(0)
                    bytes = bytes_object.read()
                    return bytes


class slack_conversation:
    def __init__(self, thread_data, bot_token, channel_id, thread_ts, bot_user_id):
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.messages = [
            slack_message(message_data, bot_token, bot_user_id)
            for message_data in thread_data
        ]


class ProcessedFile:
    def __init__(self, file_bytes):
        if not isinstance(file_bytes, bytes):
            raise ValueError("file_bytes must be an instance of bytes")
        self.mime_type = magic.from_buffer(file_bytes, mime=True)
        self.file_bytes = file_bytes


class TransformedSlackMessage:
    def __init__(self, user_id, bot_user_id):
        self.user_id = user_id
        self.bot_user_id = bot_user_id
        self.text = ""
        self.files = []

    def add_text(self, additional_text):
        if not isinstance(additional_text, str):
            raise TypeError("additional_text must be a string")
        self.text += additional_text

    def add_file(self, file):
        if not isinstance(file, ProcessedFile):
            raise TypeError("file must be an instance of ProcessedFile")
        self.files.append({"mime_type": file.mime_type, "file_bytes": file.file_bytes})


class TransformedSlackConversation:
    def __init__(self):
        self.messages = []

    def add_message(self, processed_message):
        if not isinstance(processed_message, TransformedSlackMessage):
            raise TypeError(
                "processed message must be an instance of TransformedSlackMessage"
            )
        self.messages.append(processed_message)
