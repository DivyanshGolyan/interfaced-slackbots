# from app import async_session, db
# from app.database.models import Conversation, Message, File


# async def create_conversation(bot_name, channel_id, thread_ts):
#     async with async_session as session:
#         async with session.begin():
#             conversation = Conversation(
#                 bot_name=bot_name, channel_id=channel_id, thread_ts=thread_ts
#             )
#             session.add(conversation)
#             await session.commit()
#             await session.refresh(conversation)
#             return conversation


# async def get_conversation(channel_id, thread_ts):
#     async with async_session as session:
#         result = await session.scalar(
#             db.select(Conversation).filter_by(
#                 channel_id=channel_id, thread_ts=thread_ts
#             )
#         )
#         return result


# async def create_message(
#     conversation_id,
#     sender_id,
#     sender_type,
#     bot_name,
#     message_ts,
#     responding_to_ts,
#     message_type,
#     text,
#     character_count,
# ):
#     async with async_session as session:
#         async with session.begin():
#             message = Message(
#                 conversation_id=conversation_id,
#                 sender_id=sender_id,
#                 sender_type=sender_type,
#                 bot_name=bot_name,
#                 message_ts=message_ts,
#                 responding_to_ts=responding_to_ts,
#                 message_type=message_type,
#                 text=text,
#                 character_count=character_count,
#             )
#             session.add(message)
#             await session.commit()
#             await session.refresh(message)
#             return message


# async def update_message(message_id, text, character_count):
#     async with async_session as session:
#         async with session.begin():
#             message = Message(id=message_id, text=text, character_count=character_count)
#             session.merge(message)
#             await session.commit()
#             await session.refresh(message)
#             return message


# async def get_messages_by_conversation(conversation_id):
#     async with async_session as session:
#         result = await session.execute(
#             db.select(Message).filter_by(conversation_id=conversation_id)
#         )
#         return result.scalars().all()


# async def create_file(
#     message_id,
#     file_type,
#     image_pixel_count=None,
#     video_pixel_count=None,
#     pdf_page_count=None,
#     pdf_image_pixel_count=None,
#     audio_duration_seconds=None,
# ):
#     async with async_session as session:
#         async with session.begin():
#             file = File(
#                 message_id=message_id,
#                 file_type=file_type,
#                 image_pixel_count=image_pixel_count,
#                 video_pixel_count=video_pixel_count,
#                 pdf_page_count=pdf_page_count,
#                 pdf_image_pixel_count=pdf_image_pixel_count,
#                 audio_duration_seconds=audio_duration_seconds,
#             )
#             session.add(file)
#             await session.commit()
#             await session.refresh(file)
#             return file


# async def get_files_by_message(message_id):
#     async with async_session as session:
#         result = await session.execute(db.select(File).filter_by(message_id=message_id))
#         return result.scalars().all()
