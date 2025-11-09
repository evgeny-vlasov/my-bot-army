from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.document import DocumentCreate, DocumentResponse
from app.schemas.document import Document
from app.schemas.bot import Bot
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

router = APIRouter()

# Initialize embedding service
embedding_service = EmbeddingService(api_key=settings.ANTHROPIC_API_KEY)


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a document to a bot's knowledge base.

    Automatically generates vector embedding for RAG.
    """
    # Verify bot exists
    result = await db.execute(
        select(Bot).where(Bot.id == doc_data.bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Generate embedding
    embedding = await embedding_service.get_embedding(doc_data.content)

    # Create document
    db_doc = Document(
        bot_id=doc_data.bot_id,
        title=doc_data.title,
        content=doc_data.content,
        source=doc_data.source,
        embedding=embedding,
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    return db_doc


@router.get("/{bot_id}", response_model=List[DocumentResponse])
async def list_documents(
    bot_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all documents for a bot"""
    query = (
        select(Document)
        .where(Document.bot_id == bot_id)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )

    result = await db.execute(query)
    documents = result.scalars().all()

    return documents


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document from knowledge base"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    await db.delete(document)
    await db.commit()
    return None
