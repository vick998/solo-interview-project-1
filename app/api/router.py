"""API router with chat, upload, and ask endpoints."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.schemas import (
    AddUrlsRequest,
    AddUrlsResponse,
    AskRequest,
    AskResponse,
    CreateChatRequest,
    DocumentEnabledRequest,
    UpdateChatRequest,
    UploadResponse,
)
from app.config import QA_DEFAULT_MODEL, QA_MODELS
from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import (
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    extract_text,
)
from app.extraction.url import download_from_url
from app.qa.pipeline import answer_with_history, list_models
from app.storage.chat_repository import ChatRepository
from app.storage.exceptions import ChatNotFoundError

router = APIRouter()
_repo: ChatRepository | None = None


def get_repo() -> ChatRepository:
    """Dependency that returns the chat repository. Overridable in tests."""
    global _repo
    if _repo is None:
        _repo = ChatRepository()
    return _repo


ALLOWED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


def _validate_file_extension(filename: str) -> None:
    """Raise HTTPException if file extension is not supported."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: '{suffix}'. Supported: {ALLOWED_EXTENSIONS}",
        )


def _derive_title(question: str) -> str:
    """Derive chat title from first question: 5 words, max 50 chars."""
    words = question.strip().split()[:5]
    title = " ".join(words)
    return title[:50] if len(title) > 50 else title


def _validate_model_id(model_id: str) -> None:
    """Raise HTTPException if model_id is invalid."""
    valid_ids = {m["id"] for m in QA_MODELS}
    if model_id not in valid_ids:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid model_id: '{model_id}'. Valid: {valid_ids}",
        )


@router.get("/chats")
async def list_chats(repo: ChatRepository = Depends(get_repo)) -> list[dict]:
    """List chats sorted by updated_at desc."""
    await repo.ensure_init()
    return await repo.list_chats()


@router.post("/chats")
async def create_chat(
    request: CreateChatRequest | None = None,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Create a new chat."""
    await repo.ensure_init()
    title = request.title if request else None
    chat_id = await repo.create_chat(title=title)
    return {"id": chat_id}


@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Get chat with documents and messages."""
    await repo.ensure_init()
    chat = await repo.get_chat_with_documents_and_messages(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    return chat


@router.patch("/chats/{chat_id}")
async def update_chat(
    chat_id: str,
    request: UpdateChatRequest,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Update chat title."""
    await repo.ensure_init()
    if request.title is None:
        return {"id": chat_id}
    try:
        await repo.update_chat_title(chat_id, request.title)
    except ChatNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"id": chat_id}


@router.post("/chats/{chat_id}/upload", response_model=UploadResponse)
async def upload(
    chat_id: str,
    files: list[UploadFile] = File(...),
    repo: ChatRepository = Depends(get_repo),
) -> UploadResponse:
    """Upload files to a chat. Partial success: returns document_ids and failed list."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    document_ids: list[str] = []
    failed: list[dict[str, str]] = []

    for upload_file in files:
        if not upload_file.filename:
            failed.append({"filename_or_url": "(no filename)", "error": "File has no filename"})
            continue
        try:
            _validate_file_extension(upload_file.filename)
        except HTTPException as e:
            failed.append({"filename_or_url": upload_file.filename, "error": str(e.detail)})
            continue

        content = await upload_file.read()
        if not content:
            continue

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(upload_file.filename).suffix,
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            text = extract_text(tmp_path)
            if text and text.strip():
                docs = await repo.add_documents(
                    chat_id,
                    [
                        {
                            "source_type": "file",
                            "source_path_or_url": upload_file.filename,
                            "display_name": upload_file.filename,
                            "extracted_text": text.strip(),
                            "enabled": True,
                        }
                    ],
                )
                document_ids.extend(docs)
        except (ExtractionError, UnsupportedFileTypeError) as e:
            failed.append({"filename_or_url": upload_file.filename, "error": str(e)})
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return UploadResponse(
        document_ids=document_ids,
        failed=failed if failed else None,
    )


@router.post("/chats/{chat_id}/add-urls", response_model=AddUrlsResponse)
async def add_urls(
    chat_id: str,
    request: AddUrlsRequest,
    repo: ChatRepository = Depends(get_repo),
) -> AddUrlsResponse:
    """Add documents from URLs. Partial success: returns document_ids and failed list."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    document_ids: list[str] = []
    failed: list[dict[str, str]] = []

    for url in request.urls:
        try:
            tmp_path, display_name = download_from_url(url)
            try:
                text = extract_text(tmp_path)
                if text and text.strip():
                    docs = await repo.add_documents(
                        chat_id,
                        [
                            {
                                "source_type": "url",
                                "source_path_or_url": url,
                                "display_name": display_name,
                                "extracted_text": text.strip(),
                                "enabled": True,
                            }
                        ],
                    )
                    document_ids.extend(docs)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except (ExtractionError, UnsupportedFileTypeError, Exception) as e:
            failed.append({"filename_or_url": url, "error": str(e)})

    return AddUrlsResponse(
        document_ids=document_ids,
        failed=failed if failed else None,
    )


@router.post("/chats/{chat_id}/ask", response_model=AskResponse)
async def ask(
    chat_id: str,
    request: AskRequest,
    repo: ChatRepository = Depends(get_repo),
) -> AskResponse:
    """Answer a question using documents from the chat."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")

    model_id = request.model_id or QA_DEFAULT_MODEL
    _validate_model_id(model_id)

    docs = await repo.get_documents(
        chat_id,
        enabled_only=request.document_ids is None,
        document_ids=request.document_ids,
    )
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="At least one document is required. Upload documents first.",
        )

    messages = await repo.get_messages(chat_id, limit=5)
    history = [(m["question"], m["answer"]) for m in messages]

    doc_texts = [d["extracted_text"] for d in docs if d.get("extracted_text")]
    answer_text = answer_with_history(
        request.question,
        doc_texts,
        history,
        model_id=model_id,
    )

    await repo.add_message(chat_id, request.question, answer_text, model_id)

    if not messages and chat.get("title") is None:
        title = _derive_title(request.question)
        try:
            await repo.update_chat_title(chat_id, title)
        except ChatNotFoundError:
            pass

    return AskResponse(answer=answer_text, model_used=model_id)


@router.patch("/chats/{chat_id}/documents/{document_id}")
async def update_document_enabled(
    chat_id: str,
    document_id: str,
    request: DocumentEnabledRequest,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Toggle document enabled state."""
    await repo.ensure_init()
    try:
        await repo.set_document_enabled(chat_id, document_id, request.enabled)
    except ChatNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"id": document_id, "enabled": request.enabled}


@router.get("/qa/models")
async def get_qa_models() -> list[dict]:
    """List available QA models for dropdown."""
    return list_models()


