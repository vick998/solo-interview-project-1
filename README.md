# AI Document Insight Service

A chat-based document QA application. Upload PDF or image documents (or add URLs), create multiple chats, and ask questions about your content. Uses the Hugging Face Inference API for QA. Built for the Abysalto technical interview.

## Features

- **Chat-based UI**: Multiple chats with document and message persistence
- **Document upload**: PDF and images (`.pdf`, `.png`, `.jpg`, `.jpeg`), plus URL ingestion
- **QA model selection**: Choose from several SQuAD-trained models (TinyBERT, DistilBERT, RoBERTa, BERT Large)
- **Frontend**: React + Vite, served from the same origin in production

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (or `pip install uv`)
- Node.js 18+ (for frontend dev)

### Install and Run

**Backend only:**

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

**Full app with frontend (dev):**

```bash
# Terminal 1: backend
uv sync && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: frontend (proxies API to backend)
cd frontend && npm install && npm run dev
```

For reproducible Docker builds, run `npm install` in `frontend/` and commit `package-lock.json`.

Frontend runs at `http://localhost:5173` and proxies API requests to the backend.

**Docker Compose (single command):**

```bash
docker compose up --build
```

Requires `HF_TOKEN` in `.env`. Copy from `.env.example` and add your token.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | Yes | Hugging Face token for Inference API (QA) |
| `DB_PATH` | No | SQLite path (default: `./data/chat.db`) |
| `VITE_API_URL` | No | API base URL when frontend is deployed separately |

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

**Validation scripts:**

```bash
# Run all validations (storage, extraction, QA)
uv run python scripts/validate_all.py
```

QA validation requires `HF_TOKEN`. Extraction and storage run without it.

---

## Docker

### Docker Compose (recommended)

```bash
# Create .env from example and add your HF_TOKEN
cp .env.example .env
# Edit .env and set HF_TOKEN=your_token

docker compose up --build
```

The app will be available at `http://localhost:8000`. Frontend is built into the image and served by FastAPI.

### Plain Docker

```bash
docker build -t doc-insight .
docker run -p 8000:8000 -e HF_TOKEN=your_token doc-insight
```

First build downloads EasyOCR (~500MB+); subsequent builds use cache.

---

## API

### Chat endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chats` | List chats |
| POST | `/chats` | Create chat |
| GET | `/chats/{id}` | Get chat with documents and messages |
| PATCH | `/chats/{id}` | Update chat title |
| POST | `/chats/{id}/upload` | Upload files |
| POST | `/chats/{id}/add-urls` | Add documents from URLs |
| POST | `/chats/{id}/ask` | Ask question (body: `question`, `document_ids?`, `model_id?`) |
| PATCH | `/chats/{id}/documents/{doc_id}` | Toggle document enabled |
| GET | `/qa/models` | List QA models |

### Examples

**Create chat and upload:**

```bash
CHAT_ID=$(curl -s -X POST http://localhost:8000/chats \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.id')

curl -X POST "http://localhost:8000/chats/${CHAT_ID}/upload" \
  -F "files=@sample.pdf"
```

**Ask a question:**

```bash
curl -X POST "http://localhost:8000/chats/${CHAT_ID}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

### Health

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

---

## Approach

| Component | Choice | Rationale |
|-----------|--------|------------|
| **PDF extraction** | PyMuPDF (fitz) | Fast, pure Python bindings, handles text PDFs well |
| **Image extraction** | EasyOCR | Supports English, good for scanned docs; uses torch/torchvision/transformers |
| **QA** | Hugging Face Inference API | Serverless, no local model load; multiple model options |
| **Storage** | SQLite | Chat, document, and message persistence |
| **Framework** | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| **Frontend** | React + Vite | Built into Docker image, served by FastAPI |
| **Package manager** | uv | Fast installs, lockfile, reproducible builds |

---

## Project Structure

```
abysalto-interview-project/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── router.py
│   │   ├── deps.py
│   │   ├── chats.py
│   │   ├── documents.py
│   │   ├── ask.py
│   │   └── schemas.py
│   ├── extraction/
│   │   ├── pdf.py, ocr.py, extractor.py, url.py
│   │   └── exceptions.py
│   ├── storage/
│   │   ├── db.py
│   │   ├── chat_repository.py
│   │   └── exceptions.py
│   └── qa/
│       ├── pipeline.py
│       └── preload.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── ChatSidebar.jsx, ChatHeader.jsx, MessageList.jsx
│   │   ├── InputArea.jsx, DocumentSidebar.jsx
│   │   ├── UploadModal.jsx, Toast.jsx
│   │   ├── api.js
│   │   └── main.jsx
│   └── package.json
├── tests/
├── scripts/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```
