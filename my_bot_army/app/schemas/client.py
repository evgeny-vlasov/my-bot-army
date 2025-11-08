from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, Text
from app.database import Base


class Client(Base):
    """Business clients using the platform"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)  # free, basic, pro, enterprise

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships defined in other models via backref
