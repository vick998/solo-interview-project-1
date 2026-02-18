"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas import (
    AddUrlsRequest,
    AskRequest,
    AskResponse,
    CreateChatRequest,
    DocumentEnabledRequest,
    UploadResponse,
)


def test_ask_request_valid() -> None:
    """AskRequest accepts valid question."""
    req = AskRequest(question="What is X?")
    assert req.question == "What is X?"
    assert req.document_ids is None
    assert req.model_id is None


def test_ask_request_with_optionals() -> None:
    """AskRequest accepts document_ids and model_id."""
    req = AskRequest(
        question="What?",
        document_ids=["id1"],
        model_id="tinybert",
    )
    assert req.document_ids == ["id1"]
    assert req.model_id == "tinybert"


def test_ask_request_missing_question_raises() -> None:
    """AskRequest missing question raises ValidationError."""
    with pytest.raises(ValidationError):
        AskRequest()


def test_ask_response_valid() -> None:
    """AskResponse has answer and model_used."""
    resp = AskResponse(answer="42", model_used="tinybert")
    assert resp.answer == "42"
    assert resp.model_used == "tinybert"


def test_upload_response_valid() -> None:
    """UploadResponse has document_ids and optional failed."""
    resp = UploadResponse(document_ids=["id1", "id2"])
    assert resp.document_ids == ["id1", "id2"]
    assert resp.failed is None

    resp2 = UploadResponse(
        document_ids=["id1"],
        failed=[{"filename_or_url": "x.pdf", "error": "failed"}],
    )
    assert resp2.failed == [{"filename_or_url": "x.pdf", "error": "failed"}]


def test_create_chat_request_optional_title() -> None:
    """CreateChatRequest has optional title."""
    req = CreateChatRequest()
    assert req.title is None
    req2 = CreateChatRequest(title="My Chat")
    assert req2.title == "My Chat"


def test_add_urls_request() -> None:
    """AddUrlsRequest has urls list."""
    req = AddUrlsRequest(urls=["https://example.com/a.pdf"])
    assert req.urls == ["https://example.com/a.pdf"]


def test_document_enabled_request() -> None:
    """DocumentEnabledRequest has enabled bool."""
    req = DocumentEnabledRequest(enabled=True)
    assert req.enabled is True
