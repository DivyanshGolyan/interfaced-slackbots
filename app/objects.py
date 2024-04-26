import aiohttp
import io
from app.config import *
from app.utils.file_utils import get_mime_type_from_mapping
import time
from app.database.dao import (
    create_conversation,
    create_message,
    create_file,
    update_message_text,
)


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

        mime_type_from_mapping = get_mime_type_from_mapping(
            self.filetype, self.media_display_type
        )
        self.mimetype = (
            mime_type_from_mapping
            if mime_type_from_mapping
            else file_data.get("mimetype")
        )


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


class SlackService:

    def __init__(self, bot_name):
        self.bot_name = bot_name

    async def create_conversation_from_thread(
        self, thread_data, bot_token, channel_id, thread_ts, bot_user_id
    ):
        conversation = slack_conversation(
            thread_data, bot_token, channel_id, thread_ts, bot_user_id
        )
        try:
            db_conversation = await create_conversation(
                bot_name=self.bot_name, channel_id=channel_id, thread_ts=thread_ts
            )
        except Exception as e:
            logging.error(f"Failed to create or retrieve conversation in DB: {e}")

        for message in conversation.messages:
            try:
                await self.save_message(message)
            except Exception as e:
                logging.error(f"Failed to save message {message.ts} to DB: {e}")

        return conversation

    async def save_message(self, slack_message):
        try:
            db_message = await create_message(
                channel_id=slack_message.channel_id,
                thread_ts=slack_message.thread_ts,
                sender_id=slack_message.user_id,
                bot_name=self.bot_name,
                message_ts=slack_message.ts,
                responding_to_ts=None,
                text=slack_message.text,
            )
        except Exception as e:
            logging.error(f"Failed to create message {slack_message.ts} in DB: {e}")

        for file in slack_message.files:
            mime_category = file.mimetype.split("/")[0] if file.mimetype else None
            try:
                await create_file(
                    message_ts=slack_message.ts,
                    file_type=file.filetype,
                    size=file.size,
                    mime_category=mime_category,
                    slack_file_id=file.id,
                )
            except Exception as e:
                logging.error(
                    f"Failed to create file for message {slack_message.ts} in DB: {e}"
                )


class ProcessedFile:
    def __init__(self, file_type, file_bytes, description=None, slack_file_id=None):
        if not isinstance(file_bytes, bytes):
            raise ValueError("file_bytes must be an instance of bytes")
        self.file_type = file_type
        self.file_bytes = file_bytes
        self.description = description
        self.slack_file_id = slack_file_id


class TransformedSlackMessage:
    def __init__(self, user_id, bot_user_id, message_ts):
        self.user_id = user_id
        self.bot_user_id = bot_user_id
        self.message_ts = message_ts
        self.text = ""
        self.files = []

    def add_text(self, additional_text):
        if not isinstance(additional_text, str):
            raise TypeError("additional_text must be a string")
        clean_text = additional_text.replace(TYPING_INDICATOR, "")
        self.text += clean_text

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
    def __init__(self, text=None, is_stream=False, end_of_stream=False):
        self.text = text if text else ""
        self.files = []
        self.metadata = {}
        self.is_stream = is_stream
        self.end_of_stream = end_of_stream

    def add_text(self, text):
        self.text += text

    def add_file(self, file):
        if not isinstance(file, AgentResponseFile):
            raise TypeError("file must be an instance of AgentResponseFile")
        self.files.append(file)

    def add_metadata(self, key, value):
        self.metadata[key] = value


class AgentResponseFile:

    def __init__(
        self, file_bytes, filename, properties=None, mime_type=None, title=None
    ):
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
        self.size = len(file_bytes)
        self.title = title
        self.filename = filename
        self.properties = properties
        self.mime_category = mime_type.split("/")[0] if mime_type else None
        self.file_type = self.filename.split(".")[-1]


class SlackTextMessage:

    def __init__(
        self, client, channel, thread_ts, text, user_message_ts, bot_name, bot_user_id
    ):
        self.client = client
        self.channel = channel
        self.thread_ts = thread_ts
        self.text = text
        self.user_message_ts = user_message_ts
        self.bot_name = bot_name
        self.bot_user_id = bot_user_id
        self.ts = None  # Timestamp of the message once sent
        self.last_update_time = None

    @classmethod
    async def create_and_send(
        cls,
        client,
        channel,
        thread_ts,
        text,
        typing_indicator,
        user_message_ts,
        bot_name,
        bot_user_id,
    ):
        instance = cls(
            client, channel, thread_ts, text, user_message_ts, bot_name, bot_user_id
        )
        await instance.send(typing_indicator)
        return instance

    async def send(self, typing_indicator):
        response = await self.client.chat_postMessage(
            text=self.text + typing_indicator,
            channel=self.channel,
            thread_ts=self.thread_ts,
        )
        self.ts = response.get("ts")
        self.last_update_time = time.time()
        # Create a new message in the database
        await create_message(
            channel_id=self.channel,
            thread_ts=self.thread_ts,
            sender_id=self.bot_user_id,
            bot_name=self.bot_name,
            message_ts=self.ts,
            responding_to_ts=self.user_message_ts,
            text=self.text,
        )

    async def update_and_post(self, new_text, typing_indicator, end_of_stream):
        self.text += new_text
        if not new_text or end_of_stream:
            await self.client.chat_update(
                text=self.text + typing_indicator, channel=self.channel, ts=self.ts
            )
            # Update the message text in the database
            await update_message_text(self.ts, self.text)
        else:
            current_time = time.time()
            if current_time - self.last_update_time < SLACK_MESSAGE_UPDATE_INTERVAL:
                return
            await self.client.chat_update(
                text=self.text + typing_indicator, channel=self.channel, ts=self.ts
            )
            self.last_update_time = current_time
            # Update the message text in the database
            await update_message_text(self.ts, self.text)


class SlackFileMessage:

    def __init__(
        self,
        client,
        channel,
        thread_ts,
        text,
        files,
        user_message_ts,
        bot_name,
        bot_user_id,
    ):
        self.client = client
        self.channel = channel
        self.thread_ts = thread_ts
        self.initial_comment = text if text else None
        self.file_uploads = []
        self.files = files
        for file in self.files:
            self.file_uploads.append(
                {
                    "content": file.file_bytes,
                    "filename": file.filename,
                    "title": (file.title if file.title else None),
                }
            )
        self.ts = None
        self.user_message_ts = user_message_ts
        self.bot_name = bot_name
        self.bot_user_id = bot_user_id

    @classmethod
    async def create_and_send(
        cls,
        client,
        channel,
        thread_ts,
        text,
        files,
        user_message_ts,
        bot_name,
        bot_user_id,
    ):
        instance = cls(
            client,
            channel,
            thread_ts,
            text,
            files,
            user_message_ts,
            bot_name,
            bot_user_id,
        )
        await instance.send()
        return instance

    async def send(self):
        await self.client.files_upload_v2(
            file_uploads=self.file_uploads,
            channel=self.channel,
            initial_comment=self.initial_comment,
            thread_ts=self.thread_ts,
        )

        # Create a new message in the database
        db_message = await create_message(
            channel_id=self.channel,
            thread_ts=self.thread_ts,
            sender_id=self.bot_user_id,
            bot_name=self.bot_name,
            message_ts=self.ts,
            responding_to_ts=self.user_message_ts,
            text=self.initial_comment,
        )

        # Create file entries in the database for each file
        for file in self.files:
            await create_file(
                message_ts=self.ts,
                file_type=file.file_type,
                size=file.size,
                slack_file_id=None,
                mime_category=file.mime_category,
                properties=file.properties,
            )


class SlackResponseHandler:

    def __init__(
        self, client, channel_id, thread_ts, user_message_ts, bot_name, bot_user_id
    ):
        self.client = client
        self.channel = channel_id
        self.thread_ts = thread_ts
        self.user_message_ts = user_message_ts
        self.bot_name = bot_name
        self.bot_user_id = bot_user_id
        self.messages = []
        self.typing_indicator = f"\n\n{TYPING_INDICATOR}"

    async def handle_responses(self, response_generator):
        async for agent_response in response_generator:
            if agent_response.end_of_stream:
                typing_indicator_text = ""
            else:
                typing_indicator_text = self.typing_indicator

            if agent_response.files:
                message = await SlackFileMessage.create_and_send(
                    client=self.client,
                    channel=self.channel,
                    thread_ts=self.thread_ts,
                    text=agent_response.text,
                    files=agent_response.files,
                    user_message_ts=self.user_message_ts,
                    bot_name=self.bot_name,
                    bot_user_id=self.bot_user_id,
                )
            elif not agent_response.is_stream:
                message = await SlackTextMessage.create_and_send(
                    client=self.client,
                    channel=self.channel,
                    thread_ts=self.thread_ts,
                    text=agent_response.text,
                    typing_indicator="",
                    user_message_ts=self.user_message_ts,
                    bot_name=self.bot_name,
                    bot_user_id=self.bot_user_id,
                )
            elif not self.messages:
                message = await SlackTextMessage.create_and_send(
                    client=self.client,
                    channel=self.channel,
                    thread_ts=self.thread_ts,
                    text=agent_response.text,
                    typing_indicator=typing_indicator_text,
                    user_message_ts=self.user_message_ts,
                    bot_name=self.bot_name,
                    bot_user_id=self.bot_user_id,
                )
            else:
                latest_text_message = None
                for message in reversed(self.messages):
                    if isinstance(message, SlackTextMessage):
                        latest_text_message = message
                        break
                new_accumulated_text = (
                    latest_text_message.text
                    + agent_response.text
                    + typing_indicator_text
                )
                if len(new_accumulated_text) > 3900:
                    await latest_text_message.update_and_post(
                        new_text="",
                        typing_indicator="",
                        end_of_stream=agent_response.end_of_stream,
                    )
                    message = await SlackTextMessage.create_and_send(
                        client=self.client,
                        channel=self.channel,
                        thread_ts=self.thread_ts,
                        text=agent_response.text,
                        typing_indicator=typing_indicator_text,
                        user_message_ts=self.user_message_ts,
                        bot_name=self.bot_name,
                        bot_user_id=self.bot_user_id,
                    )
                else:
                    await latest_text_message.update_and_post(
                        new_text=agent_response.text,
                        typing_indicator=typing_indicator_text,
                        end_of_stream=agent_response.end_of_stream,
                    )

            self.messages.append(message)

        self.messages.clear()
