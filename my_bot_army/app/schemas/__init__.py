from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class TestModel(Base):
    """Test model to verify database connection"""
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
