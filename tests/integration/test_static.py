"""Integration tests for static frontend serving."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import create_app
from app.storage.chat_repository import ChatRepository


@pytest.fixture
def client_no_static() -> TestClient:
    """TestClient with no static dir (static_dir=/nonexistent). Deterministic 404 for GET /."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    repo = ChatRepository(db_path=db_path)
    app = create_app(static_dir=Path("/nonexistent"))
    app.dependency_overrides[get_repo] = lambda: repo
    mock_hf = MagicMock()
    mock_hf.question_answering.return_value = [{"answer": "ok", "score": 0.9}]
    with patch("app.qa.pipeline.get_hf_client", return_value=mock_hf):
        try:
            yield TestClient(app)
        finally:
            app.dependency_overrides.clear()


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    """Create minimal static dir with index.html for SPA fallback tests."""
    index = tmp_path / "index.html"
    index.write_text(
        '<!DOCTYPE html><html><body><div id="root"></div></body></html>',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def client_with_static(static_dir: Path) -> TestClient:
    """TestClient with static dir mounted. Uses temp ChatRepository."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    repo = ChatRepository(db_path=db_path)
    app = create_app(static_dir=static_dir)
    app.dependency_overrides[get_repo] = lambda: repo
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_get_root_returns_html_when_static_exists(client_with_static: TestClient) -> None:
    """GET / returns 200 and HTML when static dir exists."""
    response = client_with_static.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<div id=\"root\">" in response.text


def test_get_root_returns_404_when_static_missing(client_no_static: TestClient) -> None:
    """GET / returns 404 when static dir does not exist (backend-only mode)."""
    response = client_no_static.get("/")
    assert response.status_code == 404


def test_api_routes_take_precedence_over_static(
    client_with_static: TestClient,
) -> None:
    """API routes return JSON, not HTML, even when static is mounted."""
    health = client_with_static.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    chats = client_with_static.get("/chats")
    assert chats.status_code == 200
    assert isinstance(chats.json(), list)
