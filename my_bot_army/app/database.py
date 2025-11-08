from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


# Dependency for getting DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_vector_index():
    """Create index for vector similarity search"""
    async with engine.begin() as conn:
        # Create index for fast vector similarity search
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx
            ON documents
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))


# Initialize database (create tables, enable pgvector)
async def init_db():
    # Import all models so they're registered with Base (inside function to avoid circular imports)
    from app.schemas import Client, Bot, Conversation, Message, Usage, Document

    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Create vector index (after tables exist)
    await create_vector_index()
