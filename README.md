# AI Document Insight Service

A chat-based document QA application. Upload PDF or image documents (or add URLs), create multiple chats, and ask questions about your content. Uses the Hugging Face Inference API for QA. Built for a technical interview.

## Features

- **Chat-based UI**: Multiple chats with document and message persistence
- **Document upload**: PDF and images (`.pdf`, `.png`, `.jpg`, `.jpeg`), plus URL ingestion
- **QA model selection**: Choose from several SQuAD-trained models (TinyBERT, RoBERTa, BERT Large)
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

**Docker:**

`HF_TOKEN` required for QA and Docker. Copy `.env.example` to `.env` and set your token.

```bash
# Docker Compose (recommended)
cp .env.example .env
# Edit .env and set HF_TOKEN=your_token
docker compose up --build

# Plain Docker
docker build -t doc-insight .
docker run -p 8000:8000 -e HF_TOKEN=your_token doc-insight
```

The app will be available at `http://localhost:8000`. Frontend is built into the image and served by FastAPI. First build downloads EasyOCR (~500MB+); subsequent builds use cache.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | Yes | Hugging Face token for Inference API (QA, NER) |
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

---

## API

Full interactive docs at `http://localhost:8000/docs`.

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

Response (create chat): `{"id": "550e8400-e29b-41d4-a716-446655440000"}`

Response (upload): `{"document_ids": ["doc-uuid"], "failed": null}`

**Ask a question:**

```bash
curl -X POST "http://localhost:8000/chats/${CHAT_ID}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

Response: `{"answer": "The main topic is...", "model_used": "tinybert", "inference_time": 0.42}`

### Health

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

---

## Approach

### Stack and Tooling

The backend is built with **FastAPI** (async, automatic OpenAPI docs, Pydantic validation), Python 3.12+, and **uv** for dependency management. Storage uses **SQLite** via aiosqlite, with a `ChatRepository` managing chats, documents, and messages. Document extraction relies on **PyMuPDF** for PDFs and **EasyOCR** for images; URL ingestion uses httpx with 10MB size and 30s timeout limits. QA and NER run on the **Hugging Face Inference API** (serverless)—four SQuAD models for QA, and dslim/bert-base-NER for entity extraction, with chunking for long text. The frontend is **React + Vite**, built into the Docker image and served by FastAPI static. The package manager **uv** provides lockfile-based, reproducible builds.

**This project was built with Cursor.** Code quality is ensured by unit and integration tests, plus ongoing review and testing by the author.

### Validation Suite

The test suite follows the structure described in [plans/comprehensive_pytest_test_suite_3c03307d.plan.md](plans/comprehensive_pytest_test_suite_3c03307d.plan.md). **Unit tests** (fast, run with `pytest -m "not slow"`) cover extraction (`tests/unit/test_extraction.py`—file-type routing, unsupported types, mocked extractors), storage (`tests/unit/test_storage.py`—ChatRepository, session isolation, add/get), the QA pipeline (`tests/unit/test_qa_pipeline.py`—empty context, `_normalize_context`, mocked HF client), the NER pipeline (`tests/unit/test_ner_pipeline.py`—entity extraction, chunking), and schemas (`tests/unit/test_schemas.py`—Pydantic validation). **Integration tests** exercise the API (`tests/integration/test_api.py`—health, chats CRUD, upload, add-urls, ask with mocked HF) and static serving (`tests/integration/test_static.py`). **Slow tests** (`@pytest.mark.slow`) require `HF_TOKEN` and `test_docs/`: `tests/integration/test_extraction_real.py` runs real PDF/OCR extraction, and `tests/integration/test_qa_real.py` runs real QA model inference.

**Validation scripts** in [scripts/](scripts/)—`validate_storage.py`, `validate_extraction.py`, `validate_qa.py`, and `validate_all.py`—provide manual sanity checks. Run them after changes to storage, extraction, or QA logic. They complement pytest: pytest is automated regression; validation scripts are quick manual checks against real components. QA validation requires `HF_TOKEN`; storage and extraction run without it.

**Fixtures** in [tests/conftest.py](tests/conftest.py) enable isolated tests. `chat_repo` provides a `ChatRepository` backed by a temp SQLite file. `client` yields a FastAPI `TestClient` with two overrides: `app.dependency_overrides[get_repo]` injects a fresh repo per test, and `get_hf_client` is patched so the QA and NER pipelines use a mock instead of the real Hugging Face API. Integration tests thus run without network or API credits. `sample_pdf_path` and `sample_pdf_bytes` supply test document data; tests skip if `test_docs/sample.pdf` is missing (generate with `scripts/generate_test_docs.py`).

### Development Phases

The project began as a simple chat backend: a minimal FastAPI app with a health endpoint, config, and uv for dependencies (Phase 1). Document extraction followed (Phase 2)—PyMuPDF for PDFs, EasyOCR for images, a file-type router, and test documents. Phase 3 added an in-memory storage layer: SessionStore with add/get, session isolation, and SessionNotFoundError for unknown sessions. The QA pipeline (Phase 4) introduced local Hugging Face transformers: TinyBERT, lazy-loaded, with chunking for long context. Phase 5 wired everything into API endpoints: POST /upload (X-Session-ID header) and POST /ask (question + session_id in JSON).

The next major shift was persistence. The [chat persistence plan](plans/chat_persistence_and_history_0d3716ef.plan.md) replaced in-memory storage with SQLite via aiosqlite. Chats, documents, and messages gained UUIDs; the API was redesigned around GET/POST/PATCH /chats, upload, add-urls, and ask with document_ids and model_id. The frontend started as a barebones "new chat + upload files" UI and evolved into multi-chat, chat history, a QA model dropdown, document toggles in the Containing tab, and URL ingestion.

Initially, models were hosted locally—transformers pipelines and EasyOCR preloaded at Docker build. The [HF Inference API migration](plans/hf_inference_api_migration_30509893.plan.md) switched QA (and later NER) to the Hugging Face Inference API: serverless, no local model load, faster startup, simpler Docker. The [NER document overview](plans/ner_document_overview_cd6b0b50.plan.md) added entity extraction at upload time and display in the Containing panel. The [comprehensive pytest suite](plans/comprehensive_pytest_test_suite_3c03307d.plan.md) established unit tests (extraction, storage, QA, NER, schemas), integration tests (API, static), and slow tests (real extraction, real QA).

| Phase | Scope | Plan |
|-------|-------|------|
| 1. Project scaffold | FastAPI app, `/health`, config, uv | [phase_1_project_scaffold](plans/phase_1_project_scaffold_b9cbaf07.plan.md) |
| 2. Document extraction | PyMuPDF, EasyOCR, extractor router, test_docs | [phase_2_document_extraction](plans/phase_2_document_extraction_6073692c.plan.md) |
| 3. Storage layer | In-memory SessionStore, add/get, session isolation | [phase_3_storage_layer](plans/phase_3_storage_layer_2f3ccae9.plan.md) |
| 4. QA pipeline | Local transformers, TinyBERT, chunking | [phase_4_qa_pipeline](plans/phase_4_qa_pipeline_406aa8a8.plan.md) |
| 5. API endpoints | POST /upload, POST /ask, X-Session-ID | [phase_5_api_endpoints](plans/phase_5_api_endpoints_5ac943c1.plan.md) |
| 6. Docker | Multi-stage Dockerfile, model preload | [phase_6_docker](plans/phase_6_docker_b6e02009.plan.md) |
| Chat persistence | SQLite, chats/documents/messages, new API | [chat_persistence_and_history](plans/chat_persistence_and_history_0d3716ef.plan.md) |
| HF Inference migration | Local models → HF Inference API | [hf_inference_api_migration](plans/hf_inference_api_migration_30509893.plan.md) |
| Frontend | React + Vite, multi-chat, model dropdown, URL | [chat_persistence](plans/chat_persistence_and_history_0d3716ef.plan.md) Phase 5 |
| NER | Entity extraction at upload, Containing panel | [ner_document_overview](plans/ner_document_overview_cd6b0b50.plan.md) |
| Test suite | Unit, integration, slow markers | [comprehensive_pytest_test_suite](plans/comprehensive_pytest_test_suite_3c03307d.plan.md) |

### Stack Card


| Component | Choice | Rationale |
|-----------|--------|------------|
| **PDF extraction** | PyMuPDF (fitz) | Fast, pure Python bindings, handles text PDFs well |
| **Image extraction** | EasyOCR | Supports English, good for scanned docs; uses torch/torchvision/transformers |
| **QA** | Hugging Face Inference API | Serverless, no local model load; multiple model options |
| **Storage** | SQLite | Chat, document, and message persistence |
| **Framework** | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| **Frontend** | React + Vite | Built into Docker image, served by FastAPI |
| **Package manager** | uv | Fast installs, lockfile, reproducible builds |

### Inference and Models

The Hugging Face Inference API client uses a **120-second timeout**. This constraint is a primary factor for design choices: document chunking, model selection (e.g. TinyBERT vs BERT Large), and context length limits are tuned to stay within it. See [benchmark/README.md](benchmark/README.md) for Model Latency Profiling.

| Model | Weights | Task | Description |
|-------|---------|------|--------------|
| **PyMuPDF (fitz)** | N/A | PDF extraction | Rule-based text extraction; no neural model. Fast, pure Python bindings. |
| **EasyOCR** | CRAFT ~79MB + CRNN | OCR | CRAFT for text detection, ResNet-based CRNN for recognition. English (`en`). Runs locally; first run downloads ~500MB+. |
| **dslim/bert-base-NER** | 110M | NER | BERT-base-cased fine-tuned on CoNLL-2003. Entity types: PER, ORG, LOC, MISC. Chunked for long text. |
| **Intel/dynamic_tinybert** | ~67M | QA | TinyBERT-6L (6 layers, 768 hidden). SQuAD 1.1. Default QA model. Dynamic sequence-length reduction; up to 3.3x speedup vs BERT. |
| **deepset/deberta-v3-base-squad2** | 184M | QA | DeBERTa v3 base. Improved attention; strong on SQuAD 2.0. |
| **deepset/electra-base-squad2** | 110M | QA | ELECTRA-base. Discriminator pre-training; efficient. |
| **deepset/roberta-large-squad2** | 355M | QA | RoBERTa large. Highest accuracy; slowest. SQuAD 2.0 EM 85.17%, F1 88.35%. |

#### Model Latency Profile

The Hugging Face Inference API enforces a **120-second timeout** per request. To inform model selection and document chunking, we benchmark QA inference times across documents of varying length. The chart below plots average inference time (seconds) vs document length (characters) for each QA model.

![QA model inference time vs document length](benchmark/inference_histogram.png)

**Low-latency models** (TinyBERT, DeBERTa v3 base, ELECTRA base) stay consistently under ~5 seconds across all document lengths tested (12.5k–45k characters). They are suitable for real-time use with minimal latency impact.

**RoBERTa large** shows a clear trade-off: inference time scales with document length—from ~7s at 13k characters to ~60s+ at 45k characters. It remains within the 120s timeout but is best reserved for shorter documents or when maximum accuracy justifies the wait.

Note: The models in use are public-access; therefore it is not always likely that our benchmark provides an exact result all-round, the latency varies with availiability of compute resources - hinging on whether the model in question is under high-load by other users of the HF Inference platform. One can observe a high or low latency on high parameter or low parameter models, making it somewhat unintuitive as compared to self-hosting, where one observes latency as a function of number of parameters.

The 120-second threshold (red dashed line) is the critical limit; models approaching it risk timeouts. Run the benchmark yourself with `uv run python benchmark/run_benchmark.py` (see [benchmark/README.md](benchmark/README.md)).

---

## Project Structure

```
solo-interview-project-1/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── hf_client.py
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
│   ├── ner/
│   │   ├── __init__.py
│   │   └── pipeline.py
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
