---
name: Phase 7 Polish README
overview: Expand the minimal README into a complete project document covering setup (uv), Docker, example API requests/responses, and an Approach section explaining tools and models.
todos: []
isProject: false
---

# Phase 7: Polish & README

## Current State

- [README.md](README.md) is minimal (2 lines)
- Project uses **uv** and [pyproject.toml](pyproject.toml) (no `requirements.txt`)
- [app/config.py](app/config.py) has `UPLOAD_DIR` and `SESSION_TIMEOUT` as constants — no env vars used
- [Dockerfile](Dockerfile) uses multi-stage build with uv, pre-downloads models at build time
- API: `POST /upload` (header `X-Session-ID`, multipart files), `POST /ask` (JSON body: `question`, `session_id`)

## Implementation Plan

### 1. Setup Instructions

Document how to run the app locally:

- **Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/) (or `pip install uv`)
- **Install:** `uv sync` (creates `.venv` and installs deps from `pyproject.toml`)
- **Run:** `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Optional env vars:** None required; note that `UPLOAD_DIR` and `SESSION_TIMEOUT` are in `app/config.py` if users want to customize

### 2. Docker Instructions

- **Build:** `docker build -t doc-insight .`
- **Run:** `docker run -p 8000:8000 doc-insight`
- Note: First build downloads models (~500MB+); subsequent builds use cache
- For upload/ask testing from host: mount test docs or use `curl` with `-F "files=@path/to/file.pdf"`

### 3. Example API Requests and Responses

**Health check:**

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

**Upload (PDF or image):**

```bash
curl -X POST http://localhost:8000/upload \
  -H "X-Session-ID: my-session-1" \
  -F "files=@test_docs/sample.pdf"
```

Response:

```json
{"message": "Documents uploaded successfully", "documents_added": 1}
```

**Ask:**

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "session_id": "my-session-1"}'
```

Response:

```json
{"answer": "The main topic is..."}
```

**Error cases:** Document 400 (missing `X-Session-ID`), 404 (unknown session), 422 (unsupported file type).

### 4. Approach Section

Briefly explain tools and models:


| Component            | Choice                                | Rationale                                            |
| -------------------- | ------------------------------------- | ---------------------------------------------------- |
| **PDF extraction**   | PyMuPDF (fitz)                        | Fast, pure Python bindings, handles text PDFs well   |
| **Image extraction** | EasyOCR                               | Supports English, good for scanned docs; lazy-loaded |
| **QA model**         | distilbert-base-cased-distilled-squad | Lightweight, runs on CPU, SQuAD-trained              |
| **Framework**        | FastAPI                               | Async, automatic OpenAPI docs, Pydantic validation   |
| **Package manager**  | uv                                    | Fast installs, lockfile, reproducible builds         |


Supported file types: `.pdf`, `.png`, `.jpg`, `.jpeg`.

### 5. README Structure (Suggested)

```markdown
# AI Document Insight Service
Brief intro (1–2 sentences)

## Setup
(uv install, run commands)

## Docker
(build, run)

## API
- GET /health
- POST /upload
- POST /ask
(With curl examples and example payloads)

## Approach
(Tools/models and rationale)

## Project Structure
(Optional: tree from DEVELOPMENT_PLAN)
```

## Validation (from Phase 7)

- Fresh clone + follow README → app runs
- README Docker instructions → container runs
- Copy-paste curl from README → valid requests

## Files to Modify


| File                   | Action                              |
| ---------------------- | ----------------------------------- |
| [README.md](README.md) | Replace with full content per above |


No new files required. The plan does not add `test_docs/sample.pdf` — the README can reference `test_docs/sample.pdf` as a placeholder; users can add their own or the repo may already include sample docs.