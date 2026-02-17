"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas import AskRequest, AskResponse, UploadResponse


def test_ask_request_valid() -> None:
    """AskRequest accepts valid question and session_id."""
    req = AskRequest(question="What is X?", session_id="s1")
    assert req.question == "What is X?"
    assert req.session_id == "s1"


def test_ask_request_missing_question_raises() -> None:
    """AskRequest missing question raises ValidationError."""
    with pytest.raises(ValidationError):
        AskRequest(session_id="s1")


def test_ask_request_missing_session_id_raises() -> None:
    """AskRequest missing session_id raises ValidationError."""
    with pytest.raises(ValidationError):
        AskRequest(question="What?")


def test_upload_response_valid() -> None:
    """UploadResponse has message and documents_added."""
    resp = UploadResponse(message="OK", documents_added=3)
    assert resp.message == "OK"
    assert resp.documents_added == 3


def test_ask_response_valid() -> None:
    """AskResponse has answer field."""
    resp = AskResponse(answer="The answer is 42")
    assert resp.answer == "The answer is 42"
