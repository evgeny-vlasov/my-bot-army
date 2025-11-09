from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_db
from app.schemas.client import Client
from app.schemas.bot import Bot
from app.schemas.conversation import Conversation
from app.schemas.usage import Usage

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall platform statistics for admin dashboard.
    """
    # Total clients
    result = await db.execute(select(func.count(Client.id)))
    total_clients = result.scalar()

    # Total bots
    result = await db.execute(select(func.count(Bot.id)))
    total_bots = result.scalar()

    # Active conversations (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.created_at >= yesterday)
    )
    active_conversations_24h = result.scalar()

    # Total usage cost
    result = await db.execute(select(func.sum(Usage.cost)))
    total_cost = result.scalar() or 0.0

    # Usage this month
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    result = await db.execute(
        select(func.sum(Usage.cost))
        .where(Usage.created_at >= first_of_month)
    )
    cost_this_month = result.scalar() or 0.0

    return {
        "total_clients": total_clients,
        "total_bots": total_bots,
        "active_conversations_24h": active_conversations_24h,
        "total_cost": round(total_cost, 2),
        "cost_this_month": round(cost_this_month, 2),
    }


@router.get("/clients/{client_id}/analytics")
async def get_client_analytics(
    client_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for a specific client.
    """
    # Verify client exists
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    since = datetime.utcnow() - timedelta(days=days)

    # Number of conversations
    result = await db.execute(
        select(func.count(Conversation.id))
        .join(Bot)
        .where(Bot.client_id == client_id)
        .where(Conversation.created_at >= since)
    )
    conversation_count = result.scalar()

    # Total usage cost
    result = await db.execute(
        select(func.sum(Usage.cost))
        .where(Usage.client_id == client_id)
        .where(Usage.created_at >= since)
    )
    total_cost = result.scalar() or 0.0

    # Tokens used
    result = await db.execute(
        select(func.sum(Usage.tokens_used))
        .where(Usage.client_id == client_id)
        .where(Usage.created_at >= since)
    )
    total_tokens = result.scalar() or 0

    return {
        "client_id": client_id,
        "client_name": client.name,
        "period_days": days,
        "conversation_count": conversation_count,
        "total_cost": round(total_cost, 2),
        "total_tokens": total_tokens,
    }
