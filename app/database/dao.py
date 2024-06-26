from app import async_session, db
from app.database.models import Conversation, Message, File, Bot
from sqlalchemy.orm import selectinload
import logging
from sqlalchemy.sql import text as sql_text
from sqlalchemy.orm import object_session

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


async def create_bot(name):
    async with async_session() as session:
        async with session.begin():
            # Check if the bot already exists using async session
            existing_bot = await session.execute(db.select(Bot).filter_by(name=name))
            existing_bot = existing_bot.scalars().first()
            if existing_bot is None:
                # Bot does not exist, create a new one
                new_bot = Bot(name=name)
                session.add(new_bot)
                await session.commit()
                return new_bot
            # Return existing bot if already in the database
            return existing_bot


async def create_conversation(bot_name, channel_id, thread_ts):
    async with async_session() as session:
        async with session.begin():
            existing_conversation = await get_conversation(channel_id, thread_ts)
            bot = await create_bot(bot_name)
            if not bot:
                raise ValueError(f"No bot found with name {bot_name}")

            if existing_conversation:
                # Ensure the bot is associated with the conversation
                if bot not in existing_conversation.bots:
                    existing_conversation.bots.append(bot)
                    await session.commit()
                    # await session.refresh(existing_conversation)
                return existing_conversation

            conversation = Conversation(channel_id=channel_id, thread_ts=thread_ts)
            conversation.bots.append(bot)
            session.add(conversation)
            await session.commit()
            # await session.refresh(conversation)
            return conversation


async def get_conversation(channel_id, thread_ts):
    async with async_session() as session:
        async with session.begin():
            result = await session.scalar(
                db.select(Conversation)
                .options(selectinload(Conversation.bots))
                .filter_by(channel_id=channel_id, thread_ts=thread_ts)
            )
            return result


async def create_message(
    channel_id,
    thread_ts,
    sender_id,
    bot_name,
    message_ts,
    responding_to_ts,
    message_type,
    text,
):
    async with async_session() as session:
        async with session.begin():
            existing_message = (
                await get_message_by_ts(message_ts) if message_ts else None
            )
            bot = await create_bot(bot_name)
            if not bot:
                raise ValueError(f"No bot found with name {bot_name}")

            if existing_message:
                # Ensure the bot is associated with the message
                if bot not in existing_message.bots:
                    existing_message.bots.append(bot)
                    await session.commit()
                    # await session.refresh(existing_message)
                return existing_message

            conversation = await create_conversation(bot_name, channel_id, thread_ts)

            message = Message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                message_ts=message_ts,
                responding_to_ts=responding_to_ts,
                message_type=message_type,
                text=text,
            )
            message.bots.append(bot)
            session.add(message)
            await session.commit()
            # await session.refresh(message)
            return message


# async def update_message_text(message_ts, new_text):
#     async with async_session() as session:
#         async with session.begin():
#             message = await get_message_by_ts(message_ts)
#             if message:
#                 logging.info(
#                     f"Updating message text for message_ts={message_ts} to '{new_text}'"
#                 )
#                 logging.info(f"Old message text: {message.text}")
#                 # Execute a manual SQL UPDATE query using text() for SQL expression
#                 await session.execute(
#                     sql_text(
#                         "UPDATE message SET text = :text WHERE message_ts = :message_ts"
#                     ),
#                     {"text": new_text, "message_ts": message_ts},
#                 )
#                 logging.info(f"New message text: {new_text}")
#                 await session.commit()
#                 # Refresh the message instance to reflect updated data
#                 # await session.refresh(message)
#                 return message
#             else:
#                 logging.info(f"No message found with message_ts={message_ts}")
#             return None


async def update_message_text(message_ts, new_text):
    async with async_session() as session:
        async with session.begin():
            message = await get_message_by_ts(message_ts)
            if message:
                if object_session(message) is not session:
                    session.add(message)  # Re-attach the object to the session

                # Update the message text
                message.text = new_text

                # Commit the transaction
                await session.commit()
                logging.info(
                    f"Updated message text committed to the database: {new_text}"
                )

                return message
            else:
                logging.info(f"No message found with message_ts={message_ts}")
            return None


async def append_message_text(message_ts, additional_text):
    async with async_session() as session:
        async with session.begin():
            message = await get_message_by_ts(message_ts)
            if message:
                message.text += additional_text
                await session.commit()
                # await session.refresh(message)
                return message
            return None


async def get_messages_by_thread_ts(thread_ts):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                db.select(Message)
                .join(Conversation)
                .filter(Conversation.thread_ts == thread_ts)
            )
            return result.scalars().all()


async def get_message_by_ts(message_ts):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                db.select(Message)
                .options(selectinload(Message.bots))
                .filter(Message.message_ts == message_ts)
            )
            message = result.scalars().first()
            logging.info(f"Retrieved message by timestamp {message_ts}: {message}")
            return message


async def create_file(
    message_ts,
    file_type,
    properties=None,
    size=0,
    slack_file_id=None,
    mime_category=None,
    message_id=None,
):
    async with async_session() as session:
        async with session.begin():
            existing_file = await session.execute(
                db.select(File).filter(File.slack_file_id == slack_file_id)
            )
            existing_file = existing_file.scalars().first()

            if existing_file:
                return existing_file

            message = await get_message_by_ts(message_ts) if message_ts else None

            # if not message:
            #     raise ValueError("No message found with the provided timestamp.")

            file = File(
                message_id=message.id if message else message_id,
                file_type=file_type,
                mime_category=mime_category,
                size=size,
                slack_file_id=slack_file_id,
                properties=properties,
            )
            session.add(file)
            await session.commit()
            # await session.refresh(file)
            return file


async def update_file(slack_file_id, properties=None, **kwargs):
    async with async_session() as session:
        async with session.begin():
            file = await session.execute(
                db.select(File).filter(File.slack_file_id == slack_file_id)
            )
            file = file.scalars().first()
            if not file:
                raise ValueError("No file found with the provided Slack file ID.")

            if object_session(file) is not session:
                session.add(file)  # Re-attach the object to the session

            # Update standard fields if provided in kwargs
            for field, value in kwargs.items():
                if hasattr(file, field) and value is not None:
                    setattr(file, field, value)

            # Update JSON properties
            if properties is not None:
                if file.properties is not None:
                    file.properties.update(properties)
                else:
                    file.properties = properties

            await session.commit()
            # await session.refresh(file)
            return file


async def get_files_by_message_ts(message_ts):
    async with async_session() as session:
        async with session.begin():
            message = await get_message_by_ts(message_ts)
            if not message:
                return []
            result = await session.execute(
                db.select(File).filter_by(message_id=message.id)
            )
            return result.scalars().all()
