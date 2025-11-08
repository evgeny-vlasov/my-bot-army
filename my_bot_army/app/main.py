from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database import get_db, init_db
from app import schemas  # Import schemas to register models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check if API and database are healthy"""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Test pgvector extension
        result = await db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        vector_version = result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "pgvector": vector_version or "installed"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }
