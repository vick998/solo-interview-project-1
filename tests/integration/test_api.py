"""Integration tests for API endpoints."""

from fastapi.testclient import TestClient


def test_get_health_returns_200(client: TestClient) -> None:
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_missing_session_id_returns_400(client: TestClient) -> None:
    """POST /upload without X-Session-ID returns 400."""
    response = client.post("/upload", files={"files": ("test.pdf", b"dummy", "application/pdf")})
    assert response.status_code == 400
    assert "Missing" in response.json()["detail"]


def test_upload_no_files_returns_error(client: TestClient) -> None:
    """POST /upload with no files returns 400 or 422."""
    response = client.post(
        "/upload",
        headers={"X-Session-ID": "s1"},
        data={},
    )
    # FastAPI validation returns 422 when files are missing
    assert response.status_code in (400, 422)
    assert "detail" in response.json()


def test_upload_file_with_no_filename_returns_error(client: TestClient) -> None:
    """POST /upload with file that has no filename returns 400 or 422."""
    response = client.post(
        "/upload",
        headers={"X-Session-ID": "s1"},
        files=[("files", (None, b"content", "application/pdf"))],
    )
    # FastAPI or our validation returns 400/422
    assert response.status_code in (400, 422)
    assert "detail" in response.json()


def test_upload_unsupported_file_type_returns_422(client: TestClient) -> None:
    """POST /upload with .txt file returns 422."""
    response = client.post(
        "/upload",
        headers={"X-Session-ID": "s1"},
        files=[("files", ("doc.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_valid_pdf_returns_200(
    client: TestClient, fresh_store, sample_pdf_bytes: bytes
) -> None:
    """POST /upload with valid PDF returns 200 and stores documents."""
    response = client.post(
        "/upload",
        headers={"X-Session-ID": "test-session"},
        files=[("files", ("sample.pdf", sample_pdf_bytes, "application/pdf"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Documents uploaded successfully"
    assert data["documents_added"] >= 1
    assert fresh_store.get_documents("test-session")


def test_ask_unknown_session_returns_404(client: TestClient) -> None:
    """POST /ask with unknown session_id returns 404."""
    response = client.post(
        "/ask",
        json={"question": "What?", "session_id": "nonexistent"},
    )
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


def test_ask_with_docs_returns_200(
    client: TestClient, fresh_store, sample_pdf_bytes: bytes
) -> None:
    """POST /ask with uploaded docs returns 200 and answer."""
    # Upload first
    client.post(
        "/upload",
        headers={"X-Session-ID": "ask-session"},
        files=[("files", ("sample.pdf", sample_pdf_bytes, "application/pdf"))],
    )
    response = client.post(
        "/ask",
        json={
            "question": "What is the expected keyword?",
            "session_id": "ask-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_ask_invalid_json_returns_422(client: TestClient) -> None:
    """POST /ask with invalid JSON returns 422."""
    response = client.post(
        "/ask",
        data="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_ask_missing_fields_returns_422(client: TestClient) -> None:
    """POST /ask with missing question or session_id returns 422."""
    response = client.post(
        "/ask",
        json={"session_id": "s1"},  # missing question
    )
    assert response.status_code == 422
