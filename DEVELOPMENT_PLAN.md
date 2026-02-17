# Development Plan: Variant A — AI Document Insight Service

This document outlines the implementation steps and validation approaches for the minimal core variant. Use it to drive development and verify each phase before proceeding.

---

## Overview

| Phase | Focus | Est. Time |
|-------|-------|-----------|
| 1 | Project scaffold | 15–30 min |
| 2 | Document extraction | 45–90 min |
| 3 | Storage layer | 20–30 min |
| 4 | QA pipeline | 45–60 min |
| 5 | API endpoints | 30–45 min |
| 6 | Docker | 30–45 min |
| 7 | Polish & README | 20–30 min |

---

## Phase 1: Project Scaffold

### Steps

1. Create `app/` directory with `__init__.py`
2. Create `app/main.py` with minimal FastAPI app and health route
3. Create `app/config.py` for settings (e.g. `UPLOAD_DIR`, `SESSION_TIMEOUT`)
4. Create `requirements.txt` with core dependencies
5. Run app locally and verify startup

### Dependencies (Phase 1)

```
fastapi
uvicorn[standard]
python-multipart
```

### Validation

| Check | How to validate |
|-------|-----------------|
| App starts | `uvicorn app.main:app --reload` exits 0, no import errors |
| Health endpoint | `curl http://localhost:8000/health` returns 200 |
| Response format | Response is JSON (e.g. `{"status": "ok"}`) |

### Validation Commands

```bash
# Terminal 1: start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: validate
curl -s http://localhost:8000/health | jq .
```

### Success Criteria

- [ ] No import or startup errors
- [ ] `GET /health` returns 200 with JSON body

---

## Phase 2: Document Extraction

### Steps

1. Create `app/extraction/` with `__init__.py`
2. Implement `app/extraction/pdf.py`: PDF path → extracted text (PyMuPDF)
3. Add image support: `app/extraction/ocr.py` (EasyOCR) or PyMuPDF for image PDFs
4. Create `app/extraction/extractor.py`: router that selects PDF vs OCR by file type
5. Add test documents to `test_docs/` (1–2 PDFs, 1 image)

### Dependencies (Phase 2)

```
PyMuPDF
# Optional for images: easyocr
```

### Validation

| Check | How to validate |
|-------|-----------------|
| PDF extraction | Call extractor on test PDF; non-empty string returned |
| Image extraction | Call extractor on test image; non-empty string returned |
| Empty/corrupt file | Graceful error or empty string, no crash |
| File type routing | PDF goes to PyMuPDF, image goes to OCR |

### Validation Script (run manually or as test)

```python
# scripts/validate_extraction.py (conceptual)
from app.extraction.extractor import extract_text

# PDF
pdf_text = extract_text("test_docs/sample.pdf")
assert len(pdf_text) > 0, "PDF should yield text"
assert "expected_keyword" in pdf_text.lower()  # if known

# Image
img_text = extract_text("test_docs/sample.png")
assert len(img_text) > 0, "Image should yield text"
```

### Validation Commands

```bash
# Quick Python one-liner (adjust path)
python -c "
from app.extraction.extractor import extract_text
t = extract_text('test_docs/sample.pdf')
print('OK' if t and len(t) > 0 else 'FAIL')
"
```

### Success Criteria

- [ ] PDF extraction returns non-empty text for valid PDF
- [ ] Image extraction returns non-empty text for valid image (if OCR added)
- [ ] Invalid/corrupt files handled without crash

---

## Phase 3: Storage Layer

### Steps

1. Create `app/storage/` with `__init__.py`
2. Implement `app/storage/session_store.py`: in-memory `dict[session_id, list[doc_text]]`
3. Define session ID source: header, query param, or auto-generated
4. Implement `add_documents(session_id, texts)` and `get_documents(session_id)`
5. Optional: persist to disk for session survival across restarts

### Validation

| Check | How to validate |
|-------|-----------------|
| Add documents | `add_documents("s1", ["text1", "text2"])` succeeds |
| Retrieve documents | `get_documents("s1")` returns `["text1", "text2"]` |
| Unknown session | `get_documents("unknown")` returns empty list or raises clear error |
| Session isolation | Docs in "s1" not visible in "s2" |

### Validation Script

```python
# Conceptual
store = SessionStore()
store.add_documents("s1", ["doc1 text", "doc2 text"])
docs = store.get_documents("s1")
assert docs == ["doc1 text", "doc2 text"]
assert store.get_documents("s2") == []  # or []
```

### Success Criteria

- [ ] Documents stored and retrieved correctly per session
- [ ] Sessions are isolated
- [ ] Unknown session returns empty or explicit error

---

## Phase 4: QA Pipeline

### Steps

1. Create `app/qa/` with `__init__.py`
2. Implement `app/qa/pipeline.py`: load QA model (e.g. `distilbert-base-cased-distilled-squad`)
3. Implement `answer(question, context)`: concatenate docs as context, run model
4. Handle empty context: return error message or fallback
5. Handle context length: truncate or chunk if > model limit (~512 tokens)

### Dependencies (Phase 4)

```
transformers
torch
```

### Validation

| Check | How to validate |
|-------|-----------------|
| Model loads | Pipeline initializes without error |
| Basic QA | `answer("What is X?", "X is defined as the main variable.")` returns "X" or similar |
| Empty context | `answer("What?", "")` returns fallback/error, no crash |
| Long context | Long context truncated or chunked; no token limit error |

### Validation Script

```python
# Conceptual
from app.qa.pipeline import answer

# Known context
ctx = "The contract expires on March 15, 2025. The vendor is Acme Corp."
ans = answer("When does the contract expire?", ctx)
assert "March" in ans or "15" in ans or "2025" in ans

# Empty
ans_empty = answer("What?", "")
assert ans_empty is not None  # fallback or error message
```

### Success Criteria

- [ ] Model loads on first call
- [ ] Answer is relevant to question and context
- [ ] Empty context handled gracefully
- [ ] Long context does not cause token overflow

---

## Phase 5: API Endpoints

### Steps

1. Implement `POST /upload`: accept multipart files, extract text, store by session
2. Implement `POST /ask`: accept `question` + `session_id`, run QA, return answer
3. Add Pydantic schemas for request/response
4. Add error handling: missing session, no documents, extraction failure
5. Add file type validation (PDF, PNG, JPG, etc.)

### Validation

| Check | How to validate |
|-------|-----------------|
| Upload | `POST /upload` with PDF returns 200, stores docs |
| Ask (with docs) | `POST /ask` returns answer based on uploaded content |
| Ask (no docs) | Returns 400/404 with clear message |
| Invalid file type | Rejected with 422 or 400 |
| Missing session | Rejected or session created; behavior documented |

### Validation Commands

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

### Success Criteria

- [ ] `POST /upload` accepts PDF(s), returns success
- [ ] `POST /ask` returns answer when docs exist
- [ ] `POST /ask` returns clear error when no docs
- [ ] Invalid inputs rejected with appropriate status codes

---

## Phase 6: Docker

### Steps

1. Create `Dockerfile`: Python base, install deps, copy app, expose port
2. Consider multi-stage build for smaller image
3. Pre-download model at build or first run
4. Add `.dockerignore` (venv, `__pycache__`, `.git`)
5. Test build and run

### Validation

| Check | How to validate |
|-------|-----------------|
| Build | `docker build -t doc-insight .` succeeds |
| Run | `docker run -p 8000:8000 doc-insight` starts without crash |
| Health | `curl http://localhost:8000/health` returns 200 from inside container |
| Upload/Ask | Same curl commands work against containerized app |

### Validation Commands

```bash
# Build
docker build -t doc-insight .

# Run (background)
docker run -d -p 8000:8000 --name doc-insight-test doc-insight

# Validate
curl -s http://localhost:8000/health
curl -X POST http://localhost:8000/upload -H "X-Session-ID: d1" -F "files=@test_docs/sample.pdf"
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What?","session_id":"d1"}'

# Cleanup
docker stop doc-insight-test && docker rm doc-insight-test
```

### Success Criteria

- [ ] Image builds without error
- [ ] Container runs and serves requests
- [ ] Upload and Ask work from host

---

## Phase 7: Polish & README

### Steps

1. Document setup: venv, pip install, env vars
2. Document Docker: build and run commands
3. Add example `curl` for `POST /upload` and `POST /ask`
4. Add example request/response payloads
5. Add "Approach" section: tools/models chosen and why

### Validation

| Check | How to validate |
|-------|-----------------|
| Fresh clone | New clone + follow README → app runs |
| Docker path | README Docker instructions → container runs |
| Examples | Copy-paste curl from README → valid requests |

### Success Criteria

- [ ] README has setup instructions
- [ ] README has Docker instructions
- [ ] README has example API requests/responses
- [ ] README has brief approach description

---

## Full Validation Checklist (Pre-Submit)

Run through all checks before considering the project complete:

```
Phase 1: [ ] App starts, /health returns 200
Phase 2: [ ] PDF extraction works, test_docs present
Phase 3: [ ] Session store add/get works, isolation verified
Phase 4: [ ] QA returns sensible answers, empty context handled
Phase 5: [ ] POST /upload and POST /ask work end-to-end
Phase 6: [ ] Docker build and run succeed
Phase 7: [ ] README complete and accurate
```

---

## Quick Reference: requirements.txt (Full)

```
fastapi
uvicorn[standard]
python-multipart
PyMuPDF
transformers
torch
```

Optional: `easyocr` for image OCR.

---

## Project Structure (Variant A)

```
abysalto-interview-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   └── extractor.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── session_store.py
│   └── qa/
│       ├── __init__.py
│       └── pipeline.py
├── test_docs/
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── README.md
└── DEVELOPMENT_PLAN.md  (this file)
```
