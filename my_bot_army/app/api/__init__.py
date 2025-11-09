from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1 import clients, bots, conversations, widget, admin, documents

api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(widget.router, prefix="/widget", tags=["widget"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
