from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse,
)
from app.schemas.conversation import Conversation, Message
from app.schemas.bot import Bot
from app.schemas.usage import Usage
from app.services.claude_service import ClaudeService
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

router = APIRouter()

# Initialize services
claude_service = ClaudeService(api_key=settings.ANTHROPIC_API_KEY)
embedding_service = EmbeddingService(api_key=settings.ANTHROPIC_API_KEY)


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new conversation with a bot.

    This is called when a user first interacts with a bot.
    """
    # Verify bot exists and is active
    result = await db.execute(
        select(Bot).where(Bot.id == conversation_data.bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if not bot.is_active or bot.deployment_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is not active"
        )

    # Create conversation
    db_conversation = Conversation(**conversation_data.model_dump())
    db.add(db_conversation)
    await db.flush()
    await db.refresh(db_conversation)

    return db_conversation


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a conversation with all its messages.
    """
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    bot_id: Optional[int] = None,
    user_identifier: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List conversations with optional filtering.
    """
    query = select(Conversation)

    if bot_id is not None:
        query = query.where(Conversation.bot_id == bot_id)

    if user_identifier is not None:
        query = query.where(Conversation.user_identifier == user_identifier)

    if is_active is not None:
        query = query.where(Conversation.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    conversations = result.scalars().all()

    return conversations


@router.post("/{conversation_id}/end", response_model=ConversationResponse)
async def end_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    End/close a conversation.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conversation.is_active = False
    conversation.ended_at = datetime.utcnow()

    await db.flush()
    await db.refresh(conversation)

    return conversation


# Chat/Message Endpoints

class ChatRequest(BaseModel):
    """Request to send a message to a bot"""
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    """Response from bot"""
    conversation_id: int
    user_message: MessageResponse
    bot_message: MessageResponse


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get a bot response.

    This is the main endpoint for chatting with bots.
    """
    # Get conversation and verify it's active
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.bot))
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == chat_request.conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if not conversation.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation is not active"
        )

    bot = conversation.bot

    if not bot.is_active or bot.deployment_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is not active"
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message,
    )
    db.add(user_message)
    await db.flush()
    await db.refresh(user_message)

    # Get bot response using Claude API with RAG
    bot_response_text, tokens_used = await get_bot_response(
        bot=bot,
        conversation_history=conversation.messages,
        user_message=chat_request.message,
        db=db,
    )

    # Save bot message
    bot_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=bot_response_text,
        tokens_used=tokens_used,
    )
    db.add(bot_message)
    await db.flush()
    await db.refresh(bot_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    await db.flush()

    # Log usage in background
    background_tasks.add_task(
        log_usage,
        db_session=db,
        client_id=bot.client_id,
        bot_id=bot.id,
        conversation_id=conversation.id,
        tokens_used=tokens_used,
    )

    return ChatResponse(
        conversation_id=conversation.id,
        user_message=user_message,
        bot_message=bot_message,
    )


async def get_bot_response(
    bot: Bot,
    conversation_history: List[Message],
    user_message: str,
    db: AsyncSession,
) -> tuple[str, int]:
    """
    Get response from bot using Claude API with RAG.

    Returns:
        Tuple of (response_text, tokens_used)
    """
    # Get relevant context from RAG
    context = await RAGService.get_context_for_query(
        db=db,
        bot_id=bot.id,
        query=user_message,
        embedding_service=embedding_service,
    )

    # Get response from Claude
    response = await claude_service.get_response(
        bot=bot,
        conversation_history=conversation_history,
        user_message=user_message,
        context=context,
    )

    # Extract usage info
    usage = response.get("usage", {})
    tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

    return response["content"], tokens_used


async def log_usage(
    db_session: AsyncSession,
    client_id: int,
    bot_id: int,
    conversation_id: int,
    tokens_used: int,
):
    """
    Log usage for billing (runs in background).
    """
    # Rough cost calculation (adjust based on actual pricing)
    cost_per_token = 0.00001  # $0.01 per 1000 tokens
    cost = tokens_used * cost_per_token

    usage_record = Usage(
        client_id=client_id,
        bot_id=bot_id,
        conversation_id=conversation_id,
        event_type="message",
        tokens_used=tokens_used,
        cost=cost,
    )

    db_session.add(usage_record)
    try:
        await db_session.commit()
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error logging usage: {e}")


# Message History Endpoints

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for a conversation.
    """
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get messages
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return messages
