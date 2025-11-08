from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1 import clients, bots, conversations, widget

api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(widget.router, prefix="/widget", tags=["widget"])
