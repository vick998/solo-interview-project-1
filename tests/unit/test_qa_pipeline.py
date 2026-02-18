"""Unit tests for QA pipeline (mocked; no real API calls)."""

from unittest.mock import MagicMock, patch

from app.qa.pipeline import (
    EMPTY_CONTEXT_FALLBACK,
    _normalize_context,
    answer,
    answer_with_history,
    list_models,
)


def test_empty_context_str_returns_fallback() -> None:
    """Empty string context returns EMPTY_CONTEXT_FALLBACK."""
    assert answer("What?", "") == EMPTY_CONTEXT_FALLBACK


def test_empty_context_list_returns_fallback() -> None:
    """Empty list context returns fallback."""
    assert answer("What?", []) == EMPTY_CONTEXT_FALLBACK


def test_normalize_context_str_strips() -> None:
    """_normalize_context strips whitespace from string."""
    assert _normalize_context("  hello  ") == "hello"


def test_normalize_context_list_concatenates() -> None:
    """_normalize_context concatenates list with double newlines."""
    assert _normalize_context(["doc1", "doc2"]) == "doc1\n\ndoc2"


def test_answer_with_mocked_client() -> None:
    """answer returns API result when client is mocked."""
    mock_result = [{"answer": "March 15, 2025", "score": 0.9}]
    mock_client = MagicMock()
    mock_client.question_answering.return_value = mock_result
    with patch("app.qa.pipeline.get_hf_client", return_value=mock_client):
        result = answer("When does the contract expire?", "The contract expires March 15.")
        assert result == "March 15, 2025"
        mock_client.question_answering.assert_called_once()


def test_answer_with_history_includes_history_in_context() -> None:
    """answer_with_history appends history to context."""
    mock_result = [{"answer": "Paris"}]
    mock_client = MagicMock()
    mock_client.question_answering.return_value = mock_result
    with patch("app.qa.pipeline.get_hf_client", return_value=mock_client):
        result = answer_with_history(
            "What is its capital?",
            "France is a country.",
            [("What country?", "France")],
            model_id="tinybert",
        )
        assert result == "Paris"
        call_kwargs = mock_client.question_answering.call_args.kwargs
        assert "Previous Q&A" in call_kwargs["context"]
        assert "What country?" in call_kwargs["context"]
        assert "France" in call_kwargs["context"]


def test_list_models_returns_id_and_name() -> None:
    """list_models returns list with id and name."""
    models = list_models()
    assert len(models) >= 1
    assert "id" in models[0]
    assert "name" in models[0]
    ids = [m["id"] for m in models]
    assert "tinybert" in ids
