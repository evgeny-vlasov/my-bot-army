from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.bot import BotCreate, BotUpdate, BotResponse
from app.schemas.bot import Bot
from app.schemas.client import Client

router = APIRouter()

@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new bot for a client.

    Goal: Complete in under 60 seconds.

    Steps:
    1. Validate client exists
    2. Create bot record
    3. Set default configuration
    4. Return bot ready for deployment
    """
    # Verify client exists
    result = await db.execute(
        select(Client).where(Client.id == bot_data.client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client is not active"
        )

    # Set default config if not provided
    default_config = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    bot_dict = bot_data.model_dump()
    if not bot_dict.get("config"):
        bot_dict["config"] = default_config
    else:
        # Merge with defaults
        bot_dict["config"] = {**default_config, **bot_dict["config"]}

    # Create bot
    db_bot = Bot(**bot_dict)
    db.add(db_bot)
    await db.flush()
    await db.refresh(db_bot)

    return db_bot

@router.get("/", response_model=List[BotResponse])
async def list_bots(
    client_id: int = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List bots with optional filtering by client.
    """
    query = select(Bot)

    if client_id is not None:
        query = query.where(Bot.client_id == client_id)

    if is_active is not None:
        query = query.where(Bot.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(Bot.created_at.desc())

    result = await db.execute(query)
    bots = result.scalars().all()

    return bots

@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific bot by ID.
    """
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    return bot

@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update bot configuration.
    """
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Update fields
    update_data = bot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    await db.flush()
    await db.refresh(bot)

    return bot

@router.post("/{bot_id}/deploy", response_model=BotResponse)
async def deploy_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy a bot (make it active and available for conversations).
    """
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if bot.deployment_status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is already deployed"
        )

    # Deploy bot
    bot.deployment_status = "active"
    bot.is_active = True
    bot.deployed_at = datetime.utcnow()

    await db.flush()
    await db.refresh(bot)

    return bot

@router.post("/{bot_id}/pause", response_model=BotResponse)
async def pause_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Pause a bot (temporarily disable without deleting).
    """
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    bot.deployment_status = "paused"
    bot.is_active = False

    await db.flush()
    await db.refresh(bot)

    return bot

@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a bot (soft delete).
    """
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    bot.deployment_status = "archived"
    bot.is_active = False

    await db.flush()

    return None
