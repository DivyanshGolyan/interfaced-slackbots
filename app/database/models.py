from app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property


class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


conversation_bot = db.Table(
    "conversation_bot",
    db.Column(
        "conversation_id",
        db.Integer,
        db.ForeignKey("conversation.id"),
        primary_key=True,
    ),
    db.Column("bot_id", db.Integer, db.ForeignKey("bot.id"), primary_key=True),
)

message_bot = db.Table(
    "message_bot",
    db.Column("message_id", db.Integer, db.ForeignKey("message.id"), primary_key=True),
    db.Column("bot_id", db.Integer, db.ForeignKey("bot.id"), primary_key=True),
)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(100), nullable=False)
    thread_ts = db.Column(db.DECIMAL(16, 6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="conversation", lazy=True)
    bots = db.relationship(
        "Bot",
        secondary=conversation_bot,
        backref=db.backref("conversations", lazy=True),
    )

    __table_args__ = (
        db.UniqueConstraint("channel_id", "thread_ts", name="unique_channel_thread"),
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=False
    )
    sender_id = db.Column(db.String(100), nullable=False)
    sender_type = db.Column(db.String(10), nullable=True)
    message_ts = db.Column(db.DECIMAL(16, 6), nullable=True)
    responding_to_ts = db.Column(db.DECIMAL(16, 6))
    message_type = db.Column(db.String(20), nullable=True)
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    text_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship("File", backref="message", lazy=True)
    bots = db.relationship(
        "Bot", secondary=message_bot, backref=db.backref("messages", lazy=True)
    )

    @hybrid_property
    def character_count(self):
        return len(self.text) if self.text else 0

    @character_count.expression
    def character_count(cls):
        return db.func.length(cls.text)

    @db.validates("text")
    def validate_text(self, key, text):
        if self.text != text:
            self.text_updated_at = datetime.utcnow()
        return text

    @hybrid_property
    def dynamic_sender_type(self):
        from app import bolt_apps  # Importing here to avoid circular imports

        bot_user_ids = {bot.get("bot_user_id") for bot in bolt_apps.values()}
        return "bot" if self.sender_id in bot_user_ids else "user"


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False)
    slack_file_id = db.Column(db.String(255), nullable=True)  # Slack file identifier
    mime_category = db.Column(db.String(20), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Integer, nullable=True)
    properties = db.Column(db.JSON)  # Store type-specific properties here
