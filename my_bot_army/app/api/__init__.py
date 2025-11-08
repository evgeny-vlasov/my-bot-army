from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1 import clients, bots

api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
