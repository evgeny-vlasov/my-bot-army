from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Document(Base):
    """Documents for RAG (knowledge base)"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document content
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)  # URL, file path, etc.

    # Vector embedding for similarity search (1536 dimensions for OpenAI embeddings)
    embedding = Column(Vector(1536), nullable=True)

    # Metadata (renamed to avoid conflict with SQLAlchemy's reserved attribute)
    doc_metadata = Column(Text, nullable=True)  # JSON string

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    bot = relationship("Bot", backref="documents")
