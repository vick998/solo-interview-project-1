"""Unit tests for NER pipeline (mocked; no real API calls)."""

from unittest.mock import MagicMock, patch

from app.ner.pipeline import extract_entities


def test_extract_entities_empty_text_returns_empty_dict() -> None:
    """Empty or whitespace-only text returns {}."""
    assert extract_entities("") == {}
    assert extract_entities("   ") == {}


def test_extract_entities_with_mocked_client() -> None:
    """extract_entities returns grouped entities when client is mocked."""
    mock_result = [
        {"entity_group": "PER", "word": "John Smith", "score": 0.99},
        {"entity_group": "ORG", "word": "Acme Corp", "score": 0.95},
        {"entity_group": "PER", "word": "Jane Doe", "score": 0.98},
    ]
    mock_client = MagicMock()
    mock_client.token_classification.return_value = mock_result
    with patch("app.ner.pipeline.get_hf_client", return_value=mock_client):
        result = extract_entities("John Smith works at Acme Corp with Jane Doe.")
        assert result == {
            "PER": ["Jane Doe", "John Smith"],
            "ORG": ["Acme Corp"],
        }
        mock_client.token_classification.assert_called_once()


def test_extract_entities_deduplicates_case_insensitive() -> None:
    """extract_entities deduplicates entities case-insensitively."""
    mock_result = [
        {"entity_group": "PER", "word": "John", "score": 0.99},
        {"entity_group": "PER", "word": "john", "score": 0.95},
    ]
    mock_client = MagicMock()
    mock_client.token_classification.return_value = mock_result
    with patch("app.ner.pipeline.get_hf_client", return_value=mock_client):
        result = extract_entities("John and john")
        assert len(result["PER"]) == 1
        assert result["PER"][0].lower() == "john"

