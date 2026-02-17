"""Unit tests for QA pipeline (mocked; no real model load)."""

from unittest.mock import patch

from app.qa.pipeline import (
    EMPTY_CONTEXT_FALLBACK,
    _normalize_context,
    answer,
)


def test_empty_context_str_returns_fallback() -> None:
    """Empty string context returns EMPTY_CONTEXT_FALLBACK."""
    assert answer("What?", "") == EMPTY_CONTEXT_FALLBACK


def test_empty_context_list_returns_fallback() -> None:
    """Empty list context returns fallback."""
    assert answer("What?", []) == EMPTY_CONTEXT_FALLBACK


def test_empty_context_list_of_empty_strings_returns_fallback() -> None:
    """List of empty strings returns fallback."""
    assert answer("What?", ["", "  ", ""]) == EMPTY_CONTEXT_FALLBACK


def test_normalize_context_str_strips() -> None:
    """_normalize_context strips whitespace from string."""
    assert _normalize_context("  hello  ") == "hello"


def test_normalize_context_list_concatenates() -> None:
    """_normalize_context concatenates list with double newlines."""
    assert _normalize_context(["doc1", "doc2"]) == "doc1\n\ndoc2"


def test_normalize_context_list_strips_and_filters_empty() -> None:
    """_normalize_context strips and filters empty strings from list."""
    assert _normalize_context(["  a  ", "", "  b  "]) == "a\n\nb"


def test_answer_with_mocked_pipeline() -> None:
    """answer returns pipeline result when pipeline is mocked."""
    mock_result = {"answer": "March 15, 2025", "score": 0.9}
    with patch("app.qa.pipeline._get_pipeline") as mock_get:
        mock_pipe = mock_get.return_value
        mock_pipe.return_value = mock_result
        result = answer("When does the contract expire?", "The contract expires March 15.")
        assert result == "March 15, 2025"
        mock_pipe.assert_called_once()
        call_kwargs = mock_pipe.call_args.kwargs
        assert call_kwargs["question"] == "When does the contract expire?"
        assert "March 15" in call_kwargs["context"]


def test_answer_pipeline_returns_empty_uses_fallback() -> None:
    """When pipeline returns empty answer, fallback is used."""
    with patch("app.qa.pipeline._get_pipeline") as mock_get:
        mock_pipe = mock_get.return_value
        mock_pipe.return_value = {}
        result = answer("What?", "Some context")
        assert result == EMPTY_CONTEXT_FALLBACK
