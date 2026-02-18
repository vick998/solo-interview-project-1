"""API router assembling chat, document, and ask sub-routers."""

from fastapi import APIRouter

from app.api.ask import router as ask_router
from app.api.chats import router as chats_router
from app.api.deps import get_repo
from app.api.documents import router as documents_router
from app.qa.pipeline import list_models

router = APIRouter()

# Nested sub-routers under /chats
router.include_router(chats_router, prefix="/chats", tags=["chats"])
router.include_router(documents_router, prefix="/chats", tags=["documents"])
router.include_router(ask_router, prefix="/chats", tags=["ask"])


@router.get("/qa/models")
async def get_qa_models() -> list[dict]:
    """List available QA models for dropdown."""
    return list_models()
