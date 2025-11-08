from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database import get_db, init_db
from app import schemas  # Import schemas to register models
from app.api import api_router
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)


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

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# API routes
app.include_router(api_router, prefix="/api/v1")


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
