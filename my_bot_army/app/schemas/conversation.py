from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base


class Conversation(Base):
    """Chat conversations between users and bots"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)

    # User identification (can be anonymous)
    user_identifier = Column(String(255), nullable=True, index=True)  # email, session_id, etc.

    # Metadata
    source = Column(String(100), nullable=True)  # web, mobile, api, etc.
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    bot = relationship("Bot", backref="conversations")


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Metadata
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation", backref="messages")
