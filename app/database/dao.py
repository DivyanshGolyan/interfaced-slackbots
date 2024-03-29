from app import db
from app.database.models import Conversation, Message


def create_conversation(user_id, channel_id, thread_ts):
    conversation = Conversation(
        user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)
    db.session.add(conversation)
    db.session.commit()
    return conversation


def get_conversation(channel_id, thread_ts):
    conversation = Conversation.query.filter_by(
        channel_id=channel_id, thread_ts=thread_ts).first()
    return conversation


def create_message(conversation_id, sender_id, content):
    message = Message(conversation_id=conversation_id,
                      sender_id=sender_id, content=content)
    db.session.add(message)
    db.session.commit()
    return message


def get_messages_by_conversation(conversation_id):
    messages = Message.query.filter_by(
        conversation_id=conversation_id).order_by(Message.created_at).all()
    return messages
