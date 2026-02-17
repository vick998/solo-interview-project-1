---
name: Phase 5 API Endpoints
overview: Implement the API layer that exposes POST /upload and POST /ask endpoints, wiring together the existing extraction, storage, and QA pipeline with Pydantic schemas and proper error handling.
todos: []
isProject: false
---

# Phase 5: API Endpoints Implementation Plan

## Current State

- **Extraction**: `[app/extraction/extractor.py](app/extraction/extractor.py)` — `extract_text(file_path)` supports PDF, PNG, JPG; raises `UnsupportedFileTypeError`, `ExtractionError`
- **Storage**: `[app/storage/session_store.py](app/storage/session_store.py)` — `SessionStore.add_documents()`, `get_documents()`; raises `SessionNotFoundError` for unknown session
- **QA**: `[app/qa/pipeline.py](app/qa/pipeline.py)` — `answer(question, context)` accepts list of strings; returns fallback for empty context
- **Main app**: `[app/main.py](app/main.py)` — Minimal FastAPI app with `GET /health` only

## Architecture

```mermaid
flowchart TB
    subgraph upload [POST /upload]
        U1[Receive multipart files] --> U2[Validate file types]
        U2 --> U3[Save to temp file]
        U3 --> U4[extract_text per file]
        U4 --> U5[store.add_documents]
        U5 --> U6[Return success]
    end

    subgraph ask [POST /ask]
        A1[Parse question + session_id] --> A2[store.get_documents]
        A2 --> A3[qa.answer]
        A3 --> A4[Return answer JSON]
    end
```



## Implementation Steps

### 1. Create API subpackage with router module

Create `app/api/` package:

- `**app/api/__init__.py**` — export router
- `**app/api/router.py**` — `APIRouter()` with `/upload` and `/ask` endpoints
- `**app/api/schemas.py**` — Pydantic models:
  - **AskRequest**: `question: str`, `session_id: str`
  - **AskResponse**: `answer: str`
  - **UploadResponse**: `message: str`, `documents_added: int`
- **Session ID source**: Use `X-Session-ID` header for upload (per validation commands). For `/ask`, use `session_id` from JSON body.
- **Singleton SessionStore**: Instantiate one `SessionStore` at module level in `router.py` (or inject via dependency).

### 3. Implement POST /upload (in router.py)

- Accept `files: list[UploadFile]` via `File(...)` (FastAPI multipart)
- Validate file extension against `PDF_EXTENSIONS | IMAGE_EXTENSIONS` from extractor; reject unsupported with 422
- For each file: write to `tempfile.NamedTemporaryFile(delete=False)`, call `extract_text(path)`, then `os.unlink` temp file
- Catch `ExtractionError` → return 422 or 400 with clear message
- Call `store.add_documents(session_id, extracted_texts)`
- Return 200 with `UploadResponse`

**Session ID**: Require `X-Session-ID` header. If missing, return 400.

### 4. Implement POST /ask (in router.py)

- Accept JSON body with `AskRequest` (question, session_id)
- Call `store.get_documents(session_id)` → catch `SessionNotFoundError` → return 404 with message like "Session not found"
- If documents exist but are empty (edge case), QA pipeline already returns fallback
- Call `answer(question, docs)` and return `AskResponse`

### 5. Error handling matrix


| Scenario                           | Status | Response                                    |
| ---------------------------------- | ------ | ------------------------------------------- |
| Upload: missing X-Session-ID       | 400    | `{"detail": "Missing X-Session-ID header"}` |
| Upload: no files / empty           | 400    | `{"detail": "No files provided"}`           |
| Upload: invalid file type          | 422    | `{"detail": "Unsupported file type: .xyz"}` |
| Upload: extraction failure         | 422    | `{"detail": "Failed to extract: ..."}`      |
| Ask: session not found             | 404    | `{"detail": "Session not found: ..."}`      |
| Ask: invalid JSON / missing fields | 422    | FastAPI auto-validation                     |


### 6. Wire router into main app

- In `[app/main.py](app/main.py)`: `from app.api import router` and `app.include_router(router)` (optionally with `prefix="/api"` if desired; plan uses no prefix for `/upload`, `/ask` at root)
- Ensure `python-multipart` is installed (already in pyproject.toml)

### 7. Final file structure

```
app/
├── api/
│   ├── __init__.py      # exports router
│   ├── router.py        # APIRouter with POST /upload, POST /ask
│   └── schemas.py       # AskRequest, AskResponse, UploadResponse
├── main.py              # app.include_router(router)
└── ...
```

## Validation (from DEVELOPMENT_PLAN.md)

```bash
# 1. Upload a PDF
curl -X POST http://localhost:8000/upload \
  -H "X-Session-ID: test-session-1" \
  -F "files=@test_docs/sample.pdf"

# 2. Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "session_id": "test-session-1"}'

# 3. Ask without upload (should fail gracefully)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What?", "session_id": "nonexistent"}'
```

## Notes

- **Temp files**: Use `tempfile.NamedTemporaryFile(delete=False)` so the file persists until we close it and extract; then `os.unlink` to clean up. Alternatively, use `UploadFile.file` if PyMuPDF/EasyOCR can read from file-like objects (check docs — PyMuPDF `fitz.open()` typically needs a path).
- **test_docs**: The plan references `test_docs/sample.pdf`. Ensure at least one test PDF exists for validation; if not, create a minimal one or document that users must provide their own.
- **CORS**: Not required for Phase 5; add in Phase 7 if needed for frontend.

