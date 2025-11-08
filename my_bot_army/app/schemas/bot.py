from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class Bot(Base):
    """AI bot instances"""
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Bot configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)

    # Settings (stored as JSON)
    config = Column(JSON, default={}, nullable=False)  # model, temperature, max_tokens, etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    deployment_status = Column(String(50), default="draft", nullable=False)  # draft, active, paused, archived

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deployed_at = Column(DateTime, nullable=True)

    # Relationships
    client = relationship("Client", backref="bots")
