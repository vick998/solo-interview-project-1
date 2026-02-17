"""In-memory session store for document texts."""

from app.storage.exceptions import SessionNotFoundError


class SessionStore:
    """In-memory store mapping session_id to list of extracted document texts."""

    def __init__(self) -> None:
        self._store: dict[str, list[str]] = {}

    def add_documents(self, session_id: str, texts: list[str]) -> None:
        """Append texts to the session's document list. Creates session if missing."""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].extend(texts)

    def get_documents(self, session_id: str) -> list[str]:
        """Return documents for session. Raises SessionNotFoundError for unknown session."""
        if session_id not in self._store:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return self._store[session_id]
