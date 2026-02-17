"""Unit tests for SessionStore."""

import pytest

from app.storage.exceptions import SessionNotFoundError
from app.storage.session_store import SessionStore


def test_add_documents_creates_session_and_stores_texts() -> None:
    """add_documents creates session and get_documents returns stored texts."""
    store = SessionStore()
    store.add_documents("s1", ["doc1", "doc2"])
    assert store.get_documents("s1") == ["doc1", "doc2"]


def test_add_documents_appends_to_existing_session() -> None:
    """add_documents appends to existing session."""
    store = SessionStore()
    store.add_documents("s1", ["doc1", "doc2"])
    store.add_documents("s1", ["doc3"])
    assert store.get_documents("s1") == ["doc1", "doc2", "doc3"]


def test_session_isolation() -> None:
    """Docs in s1 not visible in s2."""
    store = SessionStore()
    store.add_documents("s1", ["doc1 text"])
    store.add_documents("s2", ["only in s2"])
    assert store.get_documents("s1") == ["doc1 text"]
    assert store.get_documents("s2") == ["only in s2"]
    assert "only in s2" not in store.get_documents("s1")


def test_get_documents_unknown_session_raises() -> None:
    """get_documents for unknown session raises SessionNotFoundError."""
    store = SessionStore()
    with pytest.raises(SessionNotFoundError, match="Session not found"):
        store.get_documents("nonexistent")


def test_add_documents_empty_list_creates_session() -> None:
    """add_documents with empty list does not crash; session exists."""
    store = SessionStore()
    store.add_documents("s1", [])
    # Session exists; get_documents returns empty list
    assert store.get_documents("s1") == []
