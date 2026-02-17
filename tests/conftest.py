"""Pytest fixtures for the test suite."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.router import get_store
from app.main import app
from app.storage.session_store import SessionStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DOCS = PROJECT_ROOT / "test_docs"
SAMPLE_PDF = TEST_DOCS / "sample.pdf"


@pytest.fixture
def fresh_store() -> SessionStore:
    """Return a new SessionStore instance for isolated tests."""
    return SessionStore()


@pytest.fixture
def client(fresh_store: SessionStore) -> TestClient:
    """Return TestClient with dependency override for fresh SessionStore per test."""
    app.dependency_overrides[get_store] = lambda: fresh_store
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
