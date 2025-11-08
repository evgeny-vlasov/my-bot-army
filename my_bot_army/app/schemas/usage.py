from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from app.database import Base


class Usage(Base):
    """Usage tracking for billing"""
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    # Usage metrics
    event_type = Column(String(50), nullable=False)  # message, embedding, etc.
    tokens_used = Column(Integer, default=0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)  # in USD

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    client = relationship("Client", backref="usage_records")
    bot = relationship("Bot", backref="usage_records")
