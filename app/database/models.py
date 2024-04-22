# from app import db
# from datetime import datetime


# class Conversation(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     bot_name = db.Column(db.String(100), nullable=False)
#     channel_id = db.Column(db.String(100), nullable=False)
#     thread_ts = db.Column(db.DECIMAL(16, 6), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     messages = db.relationship("Message", backref="conversation", lazy=True)


# class Message(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     conversation_id = db.Column(
#         db.Integer, db.ForeignKey("conversation.id"), nullable=False
#     )
#     sender_id = db.Column(db.String(100), nullable=False)
#     sender_type = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
#     bot_name = db.Column(db.String(100), nullable=False)
#     message_ts = db.Column(db.DECIMAL(16, 6), nullable=False)
#     responding_to_ts = db.Column(db.DECIMAL(16, 6))
#     message_type = db.Column(db.String(20), nullable=False)  # 'app_mention' or 'dm'
#     text = db.Column(db.Text)
#     character_count = db.Column(db.Integer)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(
#         db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
#     )
#     files = db.relationship("File", backref="message", lazy=True)


# class File(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False)
#     file_type = db.Column(
#         db.String(20), nullable=False
#     )  # 'image', 'video', 'pdf', 'audio'
#     image_pixel_count = db.Column(db.Integer)
#     video_pixel_count = db.Column(db.Integer)
#     pdf_page_count = db.Column(db.Integer)
#     pdf_image_pixel_count = db.Column(db.Integer)
#     audio_duration_seconds = db.Column(db.Integer)
