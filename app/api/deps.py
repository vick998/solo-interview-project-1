"""Shared API dependencies."""

from app.storage.chat_repository import ChatRepository

_repo: ChatRepository | None = None


def get_repo() -> ChatRepository:
    """Dependency that returns the chat repository. Overridable in tests."""
    global _repo
    if _repo is None:
        _repo = ChatRepository()
    return _repo
