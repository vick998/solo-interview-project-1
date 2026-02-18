"""Integration tests for API endpoints."""

from fastapi.testclient import TestClient


def test_get_health_returns_200(client: TestClient) -> None:
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_chat_returns_id(client: TestClient) -> None:
    """POST /chats returns chat id."""
    response = client.post("/chats", json={})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36


def test_list_chats_returns_empty_initially(client: TestClient) -> None:
    """GET /chats returns list (may be empty)."""
    response = client.get("/chats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_chat_not_found_returns_404(client: TestClient) -> None:
    """GET /chats/{id} for nonexistent chat returns 404."""
    response = client.get("/chats/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_upload_no_chat_returns_404(client: TestClient) -> None:
    """POST /chats/{id}/upload for nonexistent chat returns 404."""
    response = client.post(
        "/chats/00000000-0000-0000-0000-000000000000/upload",
        files=[("files", ("test.pdf", b"dummy", "application/pdf"))],
    )
    assert response.status_code == 404


def test_upload_no_files_returns_400(client: TestClient) -> None:
    """POST /chats/{id}/upload with no files returns 400."""
    create = client.post("/chats", json={})
    chat_id = create.json()["id"]
    response = client.post(
        f"/chats/{chat_id}/upload",
        data={},
    )
    assert response.status_code in (400, 422)


def test_upload_valid_pdf_returns_200(
    client: TestClient, chat_repo, sample_pdf_bytes: bytes
) -> None:
    """POST /chats/{id}/upload with valid PDF returns 200 and document_ids."""
    create = client.post("/chats", json={})
    chat_id = create.json()["id"]
    response = client.post(
        f"/chats/{chat_id}/upload",
        files=[("files", ("sample.pdf", sample_pdf_bytes, "application/pdf"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_ids" in data
    assert len(data["document_ids"]) >= 1


def test_ask_unknown_chat_returns_404(client: TestClient) -> None:
    """POST /chats/{id}/ask with unknown chat returns 404."""
    response = client.post(
        "/chats/00000000-0000-0000-0000-000000000000/ask",
        json={"question": "What?"},
    )
    assert response.status_code == 404


def test_ask_no_docs_returns_400(client: TestClient) -> None:
    """POST /chats/{id}/ask with no documents returns 400."""
    create = client.post("/chats", json={})
    chat_id = create.json()["id"]
    response = client.post(
        f"/chats/{chat_id}/ask",
        json={"question": "What is the expected keyword?"},
    )
    assert response.status_code == 400


def test_ask_with_docs_returns_200(
    client: TestClient, chat_repo, sample_pdf_bytes: bytes
) -> None:
    """POST /chats/{id}/ask with uploaded docs returns 200 and answer."""
    create = client.post("/chats", json={})
    chat_id = create.json()["id"]
    client.post(
        f"/chats/{chat_id}/upload",
        files=[("files", ("sample.pdf", sample_pdf_bytes, "application/pdf"))],
    )
    response = client.post(
        f"/chats/{chat_id}/ask",
        json={
            "question": "What is the expected keyword?",
            "model_id": "distilbert",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "model_used" in data
    assert len(data["answer"]) > 0


def test_get_qa_models_returns_list(client: TestClient) -> None:
    """GET /qa/models returns list of models."""
    response = client.get("/qa/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    ids = [m["id"] for m in data]
    assert "distilbert" in ids
    assert "name" in data[0]


def test_add_urls_no_chat_returns_404(client: TestClient) -> None:
    """POST /chats/{id}/add-urls for nonexistent chat returns 404."""
    response = client.post(
        "/chats/00000000-0000-0000-0000-000000000000/add-urls",
        json={"urls": ["https://example.com/doc.pdf"]},
    )
    assert response.status_code == 404


def test_add_urls_no_urls_returns_400(client: TestClient) -> None:
    """POST /chats/{id}/add-urls with no urls returns 400."""
    create = client.post("/chats", json={})
    chat_id = create.json()["id"]
    response = client.post(
        f"/chats/{chat_id}/add-urls",
        json={"urls": []},
    )
    assert response.status_code == 400
