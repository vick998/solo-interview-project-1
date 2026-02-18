"""Chat CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import CreateChatRequest, UpdateChatRequest
from app.storage.chat_repository import ChatRepository
from app.storage.exceptions import ChatNotFoundError

from app.api.deps import get_repo

router = APIRouter()


@router.get("")
async def list_chats(repo: ChatRepository = Depends(get_repo)) -> list[dict]:
    """List chats sorted by updated_at desc."""
    await repo.ensure_init()
    return await repo.list_chats()


@router.post("")
async def create_chat(
    request: CreateChatRequest | None = None,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Create a new chat."""
    await repo.ensure_init()
    title = request.title if request else None
    chat_id = await repo.create_chat(title=title)
    return {"id": chat_id}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Get chat with documents and messages."""
    await repo.ensure_init()
    chat = await repo.get_chat_with_documents_and_messages(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    return chat


@router.patch("/{chat_id}")
async def update_chat(
    chat_id: str,
    request: UpdateChatRequest,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Update chat title."""
    await repo.ensure_init()
    if request.title is None:
        return {"id": chat_id}
    try:
        await repo.update_chat_title(chat_id, request.title)
    except ChatNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"id": chat_id}
