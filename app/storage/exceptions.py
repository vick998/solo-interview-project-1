"""Custom exceptions for session storage."""


class SessionNotFoundError(Exception):
    """Raised when get_documents is called for a non-existent session."""

    pass


class ChatNotFoundError(Exception):
    """Raised when a chat is not found."""

    pass
