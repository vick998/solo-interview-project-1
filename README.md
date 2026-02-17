# AI Document Insight Service

A REST API that ingests PDF or image documents, extracts text, and answers questions about the uploaded content using a local QA model. Built for the Abysalto technical interview.

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (or `pip install uv`)

### Install and Run

```bash
# Install dependencies (creates .venv and installs from pyproject.toml)
uv sync

# Start the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app will be available at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### Environment Variables

None required. To customize behavior, edit `app/config.py` (`UPLOAD_DIR`, `SESSION_TIMEOUT`).

---

## Testing

```bash
# Run fast tests only (unit + API integration; excludes slow model/OCR tests)
uv run pytest -m "not slow"

# Run full test suite (includes slow extraction and QA model tests)
uv run pytest

# Run with verbose output
uv run pytest -v
```

**First-time setup:** For extraction and upload tests, generate test documents:

```bash
uv run python scripts/generate_test_docs.py
```

---

## Docker

### Build

```bash
docker build -t doc-insight .
```

First build downloads models (~500MB+); subsequent builds use cache.

### Run

```bash
docker run -p 8000:8000 doc-insight
```

To test upload/ask from the host, use `curl` with `-F "files=@path/to/file.pdf"` pointing to a file on your machine.

---

## API

### GET /health

Health check.

```bash
curl -s http://localhost:8000/health
```

Response:

```json
{"status": "ok"}
```

### POST /upload

Upload one or more documents (PDF or image). Text is extracted and stored per session.

**Headers:** `X-Session-ID` (required)

**Body:** multipart form data with `files` field(s)

```bash
curl -X POST http://localhost:8000/upload \
  -H "X-Session-ID: my-session-1" \
  -F "files=@test_docs/sample.pdf"
```

Response:

```json
{"message": "Documents uploaded successfully", "documents_added": 1}
```

Supported file types: `.pdf`, `.png`, `.jpg`, `.jpeg`.

### POST /ask

Answer a question using documents from the given session.

**Body:** JSON with `question` and `session_id`

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "session_id": "my-session-1"}'
```

Response:

```json
{"answer": "The main topic is..."}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| 400 | Missing `X-Session-ID` header, no files provided, or file has no filename |
| 404 | Unknown `session_id` (no documents uploaded for that session) |
| 422 | Unsupported file type or extraction failure |

---

## Approach

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **PDF extraction** | PyMuPDF (fitz) | Fast, pure Python bindings, handles text PDFs well |
| **Image extraction** | EasyOCR | Supports English, good for scanned docs; lazy-loaded |
| **QA model** | distilbert-base-cased-distilled-squad | Lightweight, runs on CPU, SQuAD-trained |
| **Framework** | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| **Package manager** | uv | Fast installs, lockfile, reproducible builds |

---

## Project Structure

```
abysalto-interview-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── schemas.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   ├── ocr.py
│   │   └── extractor.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── session_store.py
│   └── qa/
│       ├── __init__.py
│       └── pipeline.py
├── test_docs/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── Dockerfile
├── .dockerignore
├── README.md
└── DEVELOPMENT_PLAN.md
```
