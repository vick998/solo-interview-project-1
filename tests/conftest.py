"""Pytest fixtures for the test suite."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure HF_TOKEN is set for lifespan (app startup fails without it)
os.environ.setdefault("HF_TOKEN", "test-token-for-pytest")
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import app
from app.storage.chat_repository import ChatRepository

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DOCS = PROJECT_ROOT / "test_docs"
SAMPLE_PDF = TEST_DOCS / "sample.pdf"


@pytest.fixture
def chat_repo() -> ChatRepository:
    """Return a ChatRepository backed by temp file SQLite."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    return ChatRepository(db_path=path)


@pytest.fixture
def client(chat_repo: ChatRepository) -> TestClient:
    """Return TestClient with dependency override for ChatRepository."""
    mock_hf_client = MagicMock()
    mock_hf_client.question_answering.return_value = [
        {"answer": "expected keyword", "score": 0.9}
    ]
    app.dependency_overrides[get_repo] = lambda: chat_repo
    with patch("app.qa.pipeline._get_client", return_value=mock_hf_client):
        try:
            yield TestClient(app)
        finally:
            app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_path() -> Path:
    """Path to test_docs/sample.pdf. Skips test if missing."""
    if not SAMPLE_PDF.exists():
        pytest.skip(
            f"Missing {SAMPLE_PDF}. Run: uv run python scripts/generate_test_docs.py"
        )
    return SAMPLE_PDF


@pytest.fixture
def sample_pdf_bytes(sample_pdf_path: Path) -> bytes:
    """Bytes of sample.pdf for upload tests."""
    return sample_pdf_path.read_bytes()
