"""Storage module."""

from app.storage.exceptions import ChatNotFoundError
from app.storage.chat_repository import ChatRepository

__all__ = ["ChatRepository", "ChatNotFoundError"]
