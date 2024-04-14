import aiohttp
import io
from app.config import MAX_SLACK_FILE_SIZE
from app.utils.file_utils import get_mime_type_from_url


class slack_file:
    def __init__(self, file_data):
        self.id = file_data.get("id")
        self.created = file_data.get("created")
        self.timestamp = file_data.get("timestamp")
        self.name = file_data.get("name")
        self.title = file_data.get("title")
        self.pretty_type = file_data.get("pretty_type")
        self.user = file_data.get("user")
        self.size = file_data.get("size")
        self.url_private = file_data.get("url_private")
        self.url_private_download = file_data.get("url_private_download")
        self.permalink = file_data.get("permalink")
        self.permalink_public = file_data.get("permalink_public")
        self.media_display_type = file_data.get("media_display_type")
        self.mode = file_data.get("mode")
        # Override file_type and mime_type
        if self.url_private:
            self.filetype = self.url_private.split(".")[-1]
        else:
            self.filetype = file_data.get("filetype")

        mime_type_from_url = get_mime_type_from_url(
            self.filetype, self.media_display_type
        )
        self.mimetype = mime_type_from_url if mime_type_from_url else self.mimetype


class slack_message:
    def __init__(self, message_data, bot_token, bot_user_id):
        self.bot_token = bot_token
        self.user_id = message_data.get("user")
        self.bot_user_id = bot_user_id
        self.ts = message_data.get("ts")
        self.text = message_data.get("text")
        self._files = [
            slack_file(file_data) for file_data in message_data.get("files", [])
        ]
        self._file_contents = {}

    @property
    def files(self):
        return self._files.copy()

    async def get_file_content(self, file):
        file_url = file.url_private
        file_size = file.size

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
    def __init__(self, file_type, file_bytes):
        if not isinstance(file_bytes, bytes):
            raise ValueError("file_bytes must be an instance of bytes")
        self.file_type = file_type
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
        self.files.append(file)


class TransformedSlackConversation:
    def __init__(self):
        self.messages = []

    def add_message(self, processed_message):
        if not isinstance(processed_message, TransformedSlackMessage):
            raise TypeError(
                "processed message must be an instance of TransformedSlackMessage"
            )
        self.messages.append(processed_message)


class AgentResponse:
    def __init__(self, text=None):
        self.text = text if text else ""
        self.files = []
        self.metadata = {}

    def add_text(self, text):
        self.text += text

    def add_file(self, file):
        if not isinstance(file, AgentResponseFile):
            raise TypeError("file must be an instance of AgentResponseFile")
        self.files.append(file)

    def add_metadata(self, key, value):
        self.metadata[key] = value


class AgentResponseFile:
    def __init__(self, file_bytes, title=None):
        if not isinstance(file_bytes, bytes):
            if isinstance(file_bytes, str):
                file_bytes = file_bytes.encode()
            elif hasattr(file_bytes, "read"):  # Check if it's a file-like object
                file_bytes = file_bytes.read()
                if not isinstance(file_bytes, bytes):
                    raise TypeError(
                        "file_bytes must be bytes after reading from file-like object"
                    )
            else:
                raise TypeError(
                    "file_bytes must be bytes, a string, or a file-like object"
                )
        self.file_bytes = file_bytes
        self.title = title
