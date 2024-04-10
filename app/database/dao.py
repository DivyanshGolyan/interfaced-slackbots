from app import db
from app.database.models import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Assuming db.session is an instance of AsyncSession
# If not, it should be initialized appropriately for async operations


async def create_conversation(user_id, channel_id, thread_ts):
    async with db.session() as session:
        async with session.begin():
            conversation = Conversation(
                user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)
            session.add(conversation)
            await session.commit()
            return conversation


async def get_conversation(channel_id, thread_ts):
    async with db.session() as session:
        result = await session.execute(
            Conversation.query.filter_by(channel_id=channel_id, thread_ts=thread_ts).first())
        conversation = result.scalars().first()
        return conversation


async def create_message(conversation_id, sender_id, content):
    async with db.session() as session:
        async with session.begin():
            message = Message(conversation_id=conversation_id,
                              sender_id=sender_id, content=content)
            session.add(message)
            await session.commit()
            return message


async def get_messages_by_conversation(conversation_id):
    async with db.session() as session:
        result = await session.execute(
            Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all())
        messages = result.scalars().all()
        return messages
